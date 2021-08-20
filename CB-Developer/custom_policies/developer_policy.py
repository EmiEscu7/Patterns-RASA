import zlib

import numpy as np
import pandas as pd

import base64
import json
import sys
import logging
import random as rd

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
#from rasa.core.channels.channel import InputChannel #clase que hace l rest. Me va a devolver la metadata
from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY
from rasa.shared.core.events import SlotSet
from .custom_tracker import CustomTracker
from .context_executor import ContextExecutorGoodPerson, ContextExecutorNormalPerson, ContextExecutorBadPerson
from .custom_user_bot_uttered import UserBotUttered
from .rest_custom import RestCustom
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
        self.dict_msg = {} #multitracker {"sender_id" : UserBotUttered}
        self.dic_custom_tracker = {} # {"sender": custom_tracker}
        
    
    def _give_context_executor(self):

        different_personalities = ['ContextExecutorGoodPerson', 
                                   'ContextExecutorNormalPerson',
                                   'ContextExecutorBadPerson']

        index = self.give_context_personality()
        print("PERSONALITY --->" + different_personalities[index])
        
        type = eval(different_personalities[index] + "()")
        
        self.context_executor = type

    def give_context_personality(self):
        with open("personalities.json", "r") as file:
            personality = json.load(file)[self.name]
        
        """ 
            MEDIANTE ALGUN ALGORITMO DE MACHINE LEARNING
            SE PRETENDE PREDECIR EL COMPORTAMIENTO QUE TENDRA LA PERSONA
            EN UNA CONVERSACION, DEPENDIENDO DE SU PERSONALIDAD
        """

        return rd.randint(0, 2)        

    def get_name(self):
        return self.name

    def set_name(self, name):
        """
            Este metodo ademas de setear el nombre, llama a la funcion privada _give_context_executor() que genera en base a la personalidad, COMO respondera el bot
        """
        self.name = name
        self._give_context_executor()

    def add_sender(self, sender_id):
        """ 
        Add sender to list senders
            key: integer
            value: sender_id
        """
        self.senders[len(self.senders)] = sender_id

    def set_tracker(self, sender_id, tracker: CustomTracker):
        """
            Este metodo verifica si el sender_id existe en el diccionario dic_custom_tracker.
            En caso de que no exista, lo agrega como valor de key. Por ultimo, le asigna a ese sender el tracker pasado por parametro como valor de key
        """
        #if(not self.exist_sender(sender_id)):
        #    self.add_sender(sender_id)
        self.dic_custom_tracker[sender_id] = tracker

    def get_tracker(self, sender) -> CustomTracker:
        """
            Retorno el custom tracker asociado al sender pasado por parametro
        """
        return self.dic_custom_tracker[sender]

    def exist_sender(self, sender_id):

        """ 
            Retorno True si existe el "sender_id" pasado por parametro en el diccionario que tiene los senders y sus custom tracker asociados
            
        """
        return sender_id in self.dic_custom_tracker.keys()
           
    
    def add_messege(self, sender_id, bot_predict: UserBotUttered):
        """

            This method save all message that bot recived.
            sender_id: is bot that send message.
            message: is message sended to bot.
            bot_predict: is an object that contains user input and bot prediction
        """
        self.dict_msg[sender_id] = bot_predict

    def decide_context(self) -> Dict:
        """
            This method decide that message respond

            En un futuro cada bot decidirá algún mensaje dado algún criterio personalizado.
            Ahora sólo elige uno al azar.
        """

        [rta, destiny] = self.context_executor.decide_next(self.dict_msg)
        # rta = [bot_destino, msj]. Lo mismo interruption
        return [rta, destiny]


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
        self.rtas = []
        
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
        print("SELF.ANSWERED -----------> " + str(self.answered))
        if(self.answered):
            print("self.rtas -----> " + str(self.rtas))
            if(len(self.rtas) == 1):
                self.answered = False
            rta = self.rtas.pop(0)
            result = confidence_scores_for(rta, 1.0, domain)
            return self._prediction(result)
        else:
            #Obtengo el id de la persona que envio el mensaje
            sender_id = tracker.current_state()['sender_id']

            #Obtengo un custom tracker actualizado de la conversacion.
            custom_tracker = self.obtener_tracker(sender_id, tracker)

            #verifico que los slots "sender" y "my_name" hayan sido seteados en el custom tracker. En caso de que no, los seteo.
            if(not self.slots_was_set(custom_tracker, ['sender', 'my_name'])): 
                self.set_slots(custom_tracker) 
            

            #Ya seteados los valores en el custom tracker, los obtengo.
            my_name = custom_tracker.get_slot('my_name')# name del bot
            sender = custom_tracker.get_slot('sender')# name del bot que envia el mensaje
            print("my_name: ", my_name)
            print("sender: ", sender)

            #Si soy el destino del mensaje (i_am_destiny) o soy metiche (i_am_nosy), genero una respuesta. En caso contrario, hago un action listen.
            if(self.i_am_destiny(custom_tracker) or (self.i_am_nosy(str(my_name)))):
                rta = self.generar_mensaje(custom_tracker, my_name)
            else:
                result = confidence_scores_for('action_listen', 1.0, domain)
                return self._prediction(result)


            #agrego la respuesta que le genero al sender al manejador de contexto
            self.context_manager.add_messege(sender, rta)
        
            #Agrego al context manager, el sender y el custom tracker generado para ese sender.
            self.context_manager.set_tracker(sender_id, custom_tracker)       

            # actualizo el tracker que viene como parametro
            tracker.update(custom_tracker.get_latest_event(), domain) 
            # for slot in custom_Tracker.slots: tracker.update
            tracker.update(SlotSet("my_name", custom_tracker.get_slot("my_name"))) 

            tracker.update(SlotSet("sender", custom_tracker.get_slot("sender")))
        
            #Si es el ulitmo mensaje, retorno la respuesta. Caso contrario hago action listen
            if(self.last_message(custom_tracker)):
                self.answered = True
                [self.rtas, sender_id] = self.context_manager.decide_context() 
                print("RTAS ----> " + str(self.rtas))
                result = confidence_scores_for(self.rtas.pop(0), 1.0, domain)
            else:
                result = confidence_scores_for('action_listen', 1.0, domain)

            return self._prediction(result)



    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "developer_policy.json"


    def generar_mensaje(self, custom_tracker: CustomTracker, my_name):

        """
            Agarro el intent del ultimo mensaje que tiene el custom tracker. 
            En base a mi personalidad busco el estilo del a respuesta y genero una 
            respuesta en base al intent y a la personalidad obtenidas
        """

        rta = ''
        intent = custom_tracker.get_latest_message().intent.get(INTENT_NAME_KEY)
        print("intent: ", intent)
        if(intent != "out_of_scope"): 
            style_answer = self.get_style_answer(my_name)
            rta = 'utter_'
            rta += intent + style_answer
        user_bot = UserBotUttered(custom_tracker.get_latest_message(), rta)
        return user_bot 

    def obtener_tracker(self, sender_id, tracker: DialogueStateTracker):

        """ 
            Este metodo dado un "sender id" obtiene un custom tracker para esa conversacion. Si esta conversacion ya existia, devuelve el tracker obtenido a partir del context manager, en caso contrario (no habia una conversacion previa con esa persona),se genera un nuevo.
            Independientemente de lo anterior, se utiliza "tracker" original de la conversacion (no el custom) para actualizar los campos del custom tracker

            Retorna: Un custom tracker actualizado.
        
        """

        #Si ya habia una conversacion con la persona que tiene ese id, busco el tracker 
        if(self.context_manager.exist_sender(sender_id)):
            custom_tracker = self.context_manager.get_tracker(sender_id)

        #Si no, genero un custom tracker para esa persona
        else:
            custom_tracker = CustomTracker(
                            tracker.sender_id,
                            tracker.slots.values(),
                            tracker._max_event_history,
                            tracker.sender_source,
                            tracker.is_rule_tracker
                            )
        custom_tracker.update_tracker(tracker) 
        return custom_tracker   




    def get_flag(self, tracker : CustomTracker):
        """
            Este metodo retorna el valor del flag recibido en el mensaje
            
        
        """
        var = tracker.get_latest_message()
        metadata = var.get_metadata()
        flag = metadata["flag"]
        print("ESTE ES EL VALOR DEL FLAG  "+ str(flag))        
       
        return flag


    def i_am_destiny(self, tracker: CustomTracker):
        """
            Este metodo obtiene la metadata del ultimo mensaje y verifica si este mensaje esta referido para mi
            Retorna: 1 cuando el bot que lo llama es el destino del mensaje
        """
        var = tracker.get_latest_message()
        metadata = var.get_metadata()
        print("---------> esto es metadata" + str(metadata))
        to_me = metadata["toMe"]
        print("ESTE ES EL VALOR DEL toMe  "+ str(to_me))
        return to_me



    def last_message(self, tracker : CustomTracker):
        """ 
            Retorno True cuando el flag es 1. Eso significa que es el ultimo mensaje
            
        """
        return self.get_flag(tracker) == 1

    def i_am_nosy(self, name) -> bool:  
        """
            Determina si mi personalidad es entrometida para yo responder
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
        """ 
            En el archivo personalities.json tenemos todas las personalidades de los TeamBots. Se obtiene la personalidad de "name" (parametro) y luego se genera el estilo de respuesta en base a su personalidad.
            Se utiliza tambien la funcion get_priority_mood() para darle mas relevancia a un atributo de la personalidad que a otro.


        """
        
        with open("personalities.json", "r") as file:
            personality = json.load(file)[name]
        vector_personalities = []
        for key, value in personality.items():
            vector_personalities.append(value)


        vector_personalities = self.transform_dict_to_vector(personality)   

        neighbour = self.get_neighbour(vector_personalities) #obtiene el vector + parecido
        #neighbour = [nro,[numpyArray]]
        vector = np.take(neighbour, 1)

        return np.take(vector, len(vector)-1) #retorna si era "_formal" ó "_comun" ó "_informal"
        

    def get_neighbour(self, input) -> np.ndarray:
        """
            Este algoritmo obtiene la distancia entre "vector" y todos los vectores de familia
            Retorna: Una distancia (mientras mas chica mejor, ya que queremos ver que tan parecidos son a los vectores que tenemos definidos como personalidad)
             
        """
        
        input_numpy = np.array(input)
        
        min_dist_formal = self.compare_to_neighbour(input_numpy, "_formal")
        min_dist_informal = self.compare_to_neighbour(input_numpy, "_informal")
        min_dist_comun = self.compare_to_neighbour(input_numpy, "_comun")
        
        return (min(min_dist_comun, min_dist_formal, min_dist_informal))

    def compare_to_neighbour(self, vector_input:np.ndarray, neighbour:Text) -> list:
        
        dataframe_examples = pd.read_csv(r"examples_personalities.csv",sep=';')
        min_vector = dataframe_examples.values[0] #el primero del dataframe
        min_vector_no_string = np.array(np.delete(min_vector,min_vector.size -1))
        min_dist = 0
        cant = 0

        for example in dataframe_examples.values: #example = [1,1,1,1,1,STRING]
            if(str(np.take(example, len(example)-1)) == neighbour):
                example_no_string = np.delete(example,example.size - 1) #quita el string
                dist_actual = np.linalg.norm(vector_input-example_no_string)
                if(min_dist < dist_actual):
                    min_vector = example
                min_dist += dist_actual
                cant += 1

        return [(min_dist/cant), min_vector]

    def transform_dict_to_vector(self, dict):
        vector = []
        vector.append(dict["Neuroticism"])
        vector.append(dict["Extraversion"])
        vector.append(dict["Openness"])
        vector.append(dict["Agreeableness"])
        vector.append(dict["Conscientiousness"])

        return vector

    def slots_was_set(self, tracker:CustomTracker, list_slots_to_answer) -> bool:
        """
            Dados los slots pasados en la lista "list_slots_to_answer", este metodo verifica que si el tracker pasado por parametro los tiene seteados con algun valor.  

            Nota: El metodo get_slot no es de la clase CustomTracker propia, sino que lo hereda de DialogueStateTracker

            Retorna: - Falso: Hay algun slot sin setear
                    - True: Todos los slots fueron seteados

        """
        for slot in list_slots_to_answer:
            if(tracker.get_slot(slot) == None):
                return False        
        return True

    def set_slots(self, tracker : CustomTracker):
        
        """
            If you are only interested in the first entity of a given type use next(tracker.get_latest_entity_values(&quot;my_entity_name&quot;), None). If no entity is found None is the default result

            Este metodo obtiene la primer entidad del tipo "name" del tracker original, y la setea en los Slots del tracker y el context manager.En caso de que ya hubiera un nombre seteado previamente en el context manager, lo actualiza.

            Ademas, tambien actualiza el Slot "sender" del tracker

            Retorna: No retorna nada, actualiza los valores del tracker.
        
        """

        nameTracker = next(tracker.get_latest_entity_values("name"), None)       
        if(nameTracker != None and self.context_manager.get_name() == None):
            tracker.update(SlotSet("my_name", nameTracker))
            self.context_manager.set_name(nameTracker)
        else:
            tracker.update(SlotSet("my_name", self.context_manager.get_name()))
        
        sender_id = tracker.current_state()['sender_id']
        tracker.update(SlotSet("sender",  sender_id))   
