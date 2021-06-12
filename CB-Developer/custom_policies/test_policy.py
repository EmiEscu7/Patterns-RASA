import zlib


import base64
import json
import logging

from tqdm import tqdm
from typing import Optional, Any, Dict, List, Text

import rasa.utils.io
import rasa.shared.utils.io
from rasa.shared.constants import DOCS_URL_POLICIES
from rasa.shared.core.domain import State, Domain
from rasa.shared.core.events import ActionExecuted
from rasa.core.featurizers.tracker_featurizers import (
    TrackerFeaturizer,
    MaxHistoryTrackerFeaturizer,
)
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter
from rasa.core.policies.policy import Policy, PolicyPrediction
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.generator import TrackerWithCachedStates
from rasa.shared.utils.io import is_logging_disabled
from rasa.core.constants import MEMOIZATION_POLICY_PRIORITY
#importaciones nuevas
from rasa.core.channels.channel import InputChannel #clase que hace l rest. Me va a devolver la metadata
from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY
from rasa_sdk.events import SlotSet
from rasa.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_VALUE,
    ENTITY_ATTRIBUTE_TYPE,
    ENTITY_ATTRIBUTE_GROUP,
    ENTITY_ATTRIBUTE_ROLE,
    ACTION_TEXT,
    ACTION_NAME,
    ENTITIES,
)
from .custom_tracker import CustomTracker


logger = logging.getLogger(__name__)

# temporary constants to support back compatibility
MAX_HISTORY_NOT_SET = -1
OLD_DEFAULT_MAX_HISTORY = 5

class ContextManager():

    def __init__(self):
        self.name = None
        self.senders = {} #conjunto de senders {"nro": sender_id}
        self.dict_msg = {} #multitracker {"sender_id" :{"message": message, "answer": answer}"} Si, un dict de dict
        self.dic_custom_tracker = {} # {"sender": custom_tracker}
        self.iterator = 0

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def set_tracker(self, sender_id,tracker:CustomTracker):
        if(not self.exist_sender(sender_id)):
            self.add_sender(sender_id)
        self.dic_custom_tracker[sender_id] = tracker

    def get_tracker(self, sender) -> CustomTracker:
        return self.dic_custom_tracker[sender]

    def add_sender(self, sender_id):
        """ 
        Add sender to list senders
            key: integer
            value: sender_id
        """
        self.senders[len(self.senders)] = sender_id
            

    def get_senders(self):
        """" Return list with all senders """
        return self.senders.copy()

    def exist_sender(self, sender_id):
        """ Return True if senders contains sender_id """
        return sender_id in self.senders.values()
    
    def re_randomize(self):
        if(self.iterator <= 2):
            self.iterator += 1
        elif (self.iterator >= 2000000000):
            self.iterator = 0
        else:
            self.iterator = int(4*self.iterator - self.iterator/2)
        
    
    def add_messege(self, sender_id, message, answer):
        """
            This method save all message that bot recived.
            sender_id: is bot that send message.
            message: is message sended to bot.
            answer: is utter to bot respond from message received

        """
        self.dict_msg[sender_id] = {"message": message, "answer": answer}

    def decide_context(self):
        """
            This method decide that message respond

            En un futuro cada bot decidirá algún mensaje dado algún criterio personalizado.
            Ahora sólo elige uno al azar.
        """

        if(len(self.dict_msg) > 1):
            idx = self.iterator % len(self.dict_msg)
            sender_to_respond = self.senders.get(idx)
            self.re_randomize() 
            answer = self.dict_msg.get(sender_to_respond) #answer = {"message:" 'textoA', "answer": 'textoB'}
            return answer #esto retorna {"message:" 'textoA', "answer": 'textoB'}
        else:
            answer = self.dict_msg.popitem() #esto retorna (sender_id,{"message:" 'textoA', "answer": 'textoB'})
            #answer = {"message:" 'textoA', "answer": 'textoB'}
            return answer[1] 
    
        
    def del_message(self):
        self.dict_msg = {}



class TestPolicy(Policy):

    def __init__(
        self,
        featurizer: Optional[TrackerFeaturizer] = None,
        priority: int = MEMOIZATION_POLICY_PRIORITY,
        answered: Optional[bool] = None,
        **kwargs: Any,
        ) -> None:
        super().__init__(featurizer, priority, **kwargs)
        self.answered = False
        self.context_manager = ContextManager()
        

    def train(
        self,
        training_trackers: List[TrackerWithCachedStates],
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> None:
        """Trains the policy on given training trackers.
        Args:
            training_trackers:
                the list of the :class:`rasa.core.trackers.DialogueStateTracker`
            domain: the :class:`rasa.shared.core.domain.Domain`
            interpreter: Interpreter which can be used by the polices for featurization.
        """
        pass

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> PolicyPrediction:
        print("------------> BUENO ESTE ES EL LEN EN LA POLICY AL INICIO: "+ str(len(self.context_manager.senders)))
        if(self.answered):  
            result = confidence_scores_for('action_listen', 1.0, domain)
            self.answered = False
            return self._prediction(result) 

        sender_id = tracker.current_state()['sender_id']
        
        if(self.context_manager.exist_sender(sender_id)):
            custom_tracker = self.context_manager.get_tracker(sender_id)
            
        else:
            custom_tracker = CustomTracker(
                            tracker.sender_id,
                            tracker.slots.values(),
                            tracker._max_event_history,
                            tracker.sender_source,
                            tracker.is_rule_tracker
                            )
           
        custom_tracker.update_tracker(tracker)    
        
        
        if(not self.slots_was_set(custom_tracker, ['sender', 'my_name'])): 
            self.set_slots(custom_tracker,self.context_manager) #esto setea los slots si no estan seteados
            print("------ENTRO A SETEAR LOS SLOTS-------")
        
        my_name = custom_tracker.get_slot('my_name')#name del bot
        sender = custom_tracker.get_slot('sender')#name del bot que envia el mensaje

        if(custom_tracker.latest_message.intent.get(INTENT_NAME_KEY) != "out_of_scope"): #si entendio y dio una rta coherente. CREAR EL INTENT
            style_answer = self.get_style_answer(my_name)
            rta = 'utter_'
            intent = custom_tracker.latest_message.intent.get(INTENT_NAME_KEY)
            rta += intent + style_answer
        else:
            self.answered = True
            return confidence_scores_for('action_listen', 1.0, domain)
        
        #dos prints de control        
        print("---------------------> SENDER:" + str(sender))
        print("---------------------> NOMBRE:" + str(my_name))
        
        last_message_text = custom_tracker.latest_message.text
        self.context_manager.add_messege(sender, last_message_text, rta)       

        if(self.last_message(custom_tracker)): #if is last msg choose rta
            final_answer = self.context_manager.decide_context()
            self.context_manager.del_message()
            print("LA ANSWER FINAL ES: " + final_answer.get("answer"))
            result = confidence_scores_for(final_answer.get("answer"),1.0,domain)
        else:
            result = confidence_scores_for('action_listen', 1.0, domain)

        self.answered = True
 
        self.context_manager.set_tracker(sender_id,custom_tracker)
        print("------------> BUENO ESTE ES EL LEN EN LA POLICY AL FINAL: "+ str(len(self.context_manager.senders)))
        return self._prediction(result)


    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "test_policy.json"

    def get_flag(self, tracker : CustomTracker):
        """
            This method return flag value from recived on message.
        
        """
        var = tracker.latest_message
        metadata = var.get_metadata()
        metadata2 = metadata["flag"]
        print("ESTE ES EL VALOR DEL FLAG  "+ str(metadata2))        
       
        return metadata2

    def last_message(self, tracker : CustomTracker):
        """ Return True when flag is 1. That means is last message """
        return self.get_flag(tracker) == 1

    def get_style_answer(self, name) -> Text:  
        
        with open("personalities.json", "r") as file:
            personality = json.load(file)[name]
        vector_personalities = []
        for key, value in personality.items():
            vector_personalities.append(value)

        priorty_mood = self.get_priority_mood()

        relation = float(0.0)
        for i in range(4):
            relation += vector_personalities[i] * priorty_mood[i]

        res = [ [float(0.3), "_formal"], 
                [float(0.6), "_comun"], 
                [float(1.0), "_informal"] ]
        i = 0 
        while (relation > res[i][0]):
            i+=1

        return res[i][1] #esto retorna "_formal" ó "_comun" ó "_informal" segun corresponda con la personality
        

    def get_priority_mood(self):
        """
            La idea de esta funcion es que un algoritmo de machine learning determine
            la importancia que se le deba dar a c/u de los parametros que definen el 
            estado de animo de una persona. Actualmente devolvemos un vector con unos
            pesos determinados, que modelan los valores esperados del algoritmo
        """
        return [0.35,0.4,0.1,0.05,0.3]
        

    def slots_was_set(self, tracker:CustomTracker, list_slots_to_answer) -> bool:
        for slot in list_slots_to_answer:
            if(tracker.get_slot(slot) == None):
                return False        
        return True


    def set_slots(self, tracker : CustomTracker, context_manager: ContextManager):

        nameTracker = next(tracker.get_latest_entity_values("name"), None)
        if(nameTracker != None and context_manager.get_name() == None):
            context_manager.set_name(nameTracker)
            tracker.set_slot("my_name", nameTracker)   
        else:
            tracker.set_slot("my_name", context_manager.get_name())
            
            
        test = tracker.get_slot('my_name')
        print("NOMBRE GUARDADO: " + str(test))       
        sender_id = tracker.current_state()['sender_id']
        tracker.set_slot("sender", sender_id)   
        #self.context_manager.add_sender(sender_id)
        test2 = tracker.get_slot('sender')
        print("SENDER GUARDADO: " + str(test2))    

        
    """
    comentarios de la politica generales y auxiliares
      result = self._default_predictions(domain)
      sender_id = tracker.sender_id
      print("sender ID =" + sender_id2)
      latest = tracker.latest_message.get('text')
      print("latest: "+ latest)
      intent = tracker.latest_message.intent.get(INTENT_NAME_KEY)
      and intent == 'presentation_user'):
      nombrev2 = tracker.current_state()['name']
      print("----> nombrev2" + nombrev2)
        
    if (sender != my_name): #si el que envio el mensaje es distinto a mí, debo responder
        #agg que si el mensaje esta destinado a una persona y yo no soy esa persona, no debería respoder
        #agg tambien a lo anterior que si soy atrevido y me gusta entrometerme pueda o no meterme en la conversacion
        if(not self.answered): 
            if (intent == 'doYouHaveProblem'): #esto es porque un developer puede tener un problema y debe responder como dicta su estilo de animo
                prox = 'action_tipo' + style_answer 
                result = confidence_scores_for(prox,1.0,domain)
            
            elif(intent == 'agradecimiento'): #esto es para que corte y dejen de hablar, que de una respuesta vacia = ''
                result = confidence_scores_for('action_listen', 1.0, domain)
            
            else:    
                result = confidence_scores_for(rta, 1.0, domain)
                
            self.answered = True
        
        else:
            self.answered = False
    
        else:
            result = confidence_scores_for('action_listen', 1.0, domain)
            self.answered = True
    """
