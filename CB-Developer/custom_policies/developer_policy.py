import zlib


import base64
import json
import sys
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
from rasa.shared.core.events import SlotSet
from .custom_tracker import CustomTracker
#from .custom_tracker import CustomTracker
from rasa.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_VALUE,
    ENTITY_ATTRIBUTE_TYPE,
    ENTITY_ATTRIBUTE_GROUP,
    ENTITY_ATTRIBUTE_ROLE,
    ACTION_TEXT,
    ACTION_NAME,
    ENTITIES,
)
from rasa.shared.core.constants import (
    ACTION_LISTEN_NAME,
    LOOP_NAME,
    SHOULD_NOT_BE_SET,
    PREVIOUS_ACTION,
    ACTIVE_LOOP,
    LOOP_REJECTED,
    TRIGGER_MESSAGE,
    LOOP_INTERRUPTED,
    ACTION_SESSION_START_NAME,
    FOLLOWUP_ACTION,
)


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
        self.respondio = False

    def give_sender(self):
        return self.respondio
    
    def change_give_sender(self):
        self.respondio = not self.respondio

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def set_tracker(self, sender_id, tracker:CustomTracker):
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

    def decide_context(self) -> Dict:
        """
            This method decide that message respond

            En un futuro cada bot decidirá algún mensaje dado algún criterio personalizado.
            Ahora sólo elige uno al azar.
        """
        print("ESTE ES EL DICT MESSAGE --> " + str(self.dict_msg))
        if(len(self.dict_msg) > 1):
            idx = self.iterator % len(self.dict_msg)
            if(idx == 0):
                idx += 1
            sender_to_respond = self.senders.get(idx)
            self.re_randomize() 
            answer = self.dict_msg.get(sender_to_respond) #answer = {"message:" 'textoA', "answer": 'textoB'}
            return answer #esto retorna {"message:" 'textoA', "answer": 'textoB'}
        else:
            answer = list(self.dict_msg.values()) #esto retorna (sender_id,{"message:" 'textoA', "answer": 'textoB'})
            return answer.pop()   

    def del_message(self):
        self.dict_msg = {}


class DeveloperPolicy(Policy):

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

        """if(self.answered and self.context_manager.give_sender()):
            if (tracker.latest_action_name != 'utter_send_destination'):
                result = confidence_scores_for('utter_send_destination', 1.0, domain)
                self.answered = True
            else:
                result = confidence_scores_for('action_listen', 1.0, domain)
                self.answered = False
            return self._prediction(result)
        else:"""
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
            self.set_slots(custom_tracker) #esto setea los slots si no estan seteado 
        
        my_name = custom_tracker.get_slot('my_name')#name del bot
        sender = custom_tracker.get_slot('sender')#name del bot que envia el mensaje
        #dos prints de control        
        print("---------------------> SENDER:" + str(sender))
        print("---------------------> NOMBRE:" + str(my_name))

        if(self.i_am_destiny(custom_tracker) or (self.i_am_nosy(str(my_name)))):
            if(custom_tracker.get_latest_message().intent.get(INTENT_NAME_KEY) != "out_of_scope"): #si entendio y dio una rta coherente. CREAR EL INTENT
                style_answer = self.get_style_answer(my_name)
                rta = 'utter_'
                intent = custom_tracker.get_latest_message().intent.get(INTENT_NAME_KEY)
                rta += intent + style_answer
        else:
            result = confidence_scores_for('action_listen', 1.0, domain)
            return self._prediction(result)
        


        last_message_text = custom_tracker.get_latest_message().text
        self.context_manager.add_messege(sender, last_message_text, rta)
        """
        HASTA ACA RECIBO UN MSJ Y LO PROCESO
        ------------------------------------------------------------
        A PARTIR DE ACA VEO SI TENGO QUE CONTESTAR O SIGO ESCUCHANDO
        """
        result = self._default_predictions(domain)
        print("ANTES DEL SELF.ANSWERED")
        if(not self.answered):
            print("DENTRO DEL SELF.ANSWERED")
            if(self.context_manager.give_sender()):
                print("ENTRO A GIVE SENDER")
                rta = 'utter_send_destination'
                self.context_manager.change_give_sender()
                self.answered = True
            elif(self.last_message(custom_tracker)): #if is last msg choose rta
                print("GENERANDO RESPUESTA...")
                final_answer = self.context_manager.decide_context()
                self.context_manager.del_message()
                self.context_manager.change_give_sender()
                print("LA ANSWER FINAL ES: " + str(final_answer.get("answer")))
                rta = str(final_answer.get("answer"))                
            else:
                print("DESPUES DEL SELF.ANSWERED")
                self.answered = False
                rta = 'action_listen'
        else:
            rta = 'action_listen'
            self.answered = False
        print("DESPUES DEL SELF.ANSWERED")

        result =  confidence_scores_for(rta, 1.0, domain)

        self.context_manager.set_tracker(sender_id, custom_tracker)
        
        tracker.update(custom_tracker.get_latest_event(), domain) #actualiza el tracker que viene como parametro
        tracker.update(SlotSet("my_name",custom_tracker.get_slot("my_name"))) #for slot in custom_Tracker.slots: tracker.update
        tracker.update(SlotSet("sender", custom_tracker.get_slot("sender")))
        #self.context_manager.change_give_sender()        

        return self._prediction(result)



    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "developer_policy.json"

    def get_flag(self, tracker : CustomTracker):
        """
            This method return flag value from recived on message.
        
        """
        var = tracker.get_latest_message()
        metadata = var.get_metadata()
        flag = metadata["flag"]
        print("ESTE ES EL VALOR DEL FLAG  "+ str(flag))        
       
        return flag


    def i_am_destiny(self, tracker: CustomTracker):
        """
            This method return 1 when the bot is the destiny.
        """
        var = tracker.get_latest_message()
        metadata = var.get_metadata()
        print("---------> esto es metadata" + str(metadata))
        to_me = metadata["toMe"]
        print("ESTE ES EL VALOR DEL toMe  "+ str(to_me))
        return to_me



    def last_message(self, tracker : CustomTracker):
        """ Return True when flag is 1. That means is last message """
        return self.get_flag(tracker) == 1

    def i_am_nosy(self, name) -> bool:  
        """
            determina si mi personalidad es entrometida para yo responder
            cuando no soy el destinatario del input
            Actualmente funciona con el personalities.json que tiene un atributo
            que dice true/false si es nosy o no.
            A futuro, deberia ser un algoritmo de matchine learning que determine
            la personalidad de un bot tal que pueda tener este comportamiento de 
            entrometido en la conversacion y responder cuando no le toca.
        """ 
        with open("personalities.json", "r") as file:
            personality = json.load(file)[name]
        for key, value in personality.items():
            if(key == "nosy"):
                return value

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

    def set_slots(self, tracker : CustomTracker):

        nameTracker = next(tracker.get_latest_entity_values("name"), None)       
        if(nameTracker != None and self.context_manager.get_name() == None):
            tracker.update(SlotSet("my_name", nameTracker))
            self.context_manager.set_name(nameTracker)
        else:
            tracker.update(SlotSet("my_name", self.context_manager.get_name()))
            
        sender_id = tracker.current_state()['sender_id']
        tracker.update(SlotSet("sender",  sender_id))   

      
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
