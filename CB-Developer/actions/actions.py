# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, SessionStarted, ActionExecuted, EventType
from random import random

#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
class Respuesta(Action):

    def name(self) -> Text:
        return "action_dar_respuesta"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        res = [ [float(0.5), "_yes"],
                [float(1.0), "_no"] ] 

        rta = "utter_my_problem"      
       
        nro = round(random(), 2)
        print(nro)
        i = 0
        while(nro > res[i][0]):
            i+=1
        rta += res[i][1]

        tipo = tracker.get_slot('tipoRta')
        rta += tipo
        
    #    sender_id = tracker.current_state()['sender_id']
    #    print("SENDER1:"+sender_id)

     #   name = tracker.get_slot("name")
     #   print("name inicial"+name)
     #   tracker._set_slot("name",'testeo')
     #   name = tracker.get_slot("name")
     #   print("name cambiado"+name)

        dispatcher.utter_message(template = rta)
        return[]

class RespuestaFormal(Action):

    def name(self) -> Text:
        return 'action_tipo_formal'
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        rta = "_formal"
 
        #dispatcher.utter_message(template = rta)

        return [SlotSet("tipoRta", rta), FollowupAction("action_dar_respuesta")]

class RespuestaComun(Action):

    def name(self) -> Text:
        return 'action_tipo_comun'
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        rta = "_comun"
        #dispatcher.utter_message(template = rta)

        return [SlotSet("tipoRta", rta), FollowupAction("action_dar_respuesta")]

class RespuestaInformal(Action):

    def name(self) -> Text:
        return 'action_tipo_informal'
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        rta = "_informal"
        #dispatcher.utter_message(template = rta)

        return [SlotSet("tipoRta", rta), FollowupAction("action_dar_respuesta")]


class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"
    
    @staticmethod
    def fetch_slots(tracker: Tracker) -> List[EventType]:
        """Collect slots that contain the user's name and phone number."""

        #nombres = [ [0.3 , 'Emiliano'],
        #            [0.6 , 'Pedro'],
        #            [1.0 , 'MatiasB'] ]
        #nro = round(random(), 2)

        #i = 0
        #while(nro > nombres[i][0]):
        #    i+=1
        #nombre = nombres[i][1]
        #print(nombre)

        slots = []
        sender_id = tracker.current_state()['sender_id']
        #print(sender_id)
        #print("----> Action seasion start:" + sender_id)
        #logger.info("keeping only name/phone_number slots")
        #for key in ("username"):
        #    value = tracker.get_slot(key)
        #    if value is not None:
        #nombre = tracker.get_slot('name')
        #if(nombre == None):
        slots.append(SlotSet("name", sender_id))
        #else:
        #    slots.append(SlotSet("name", nombre))
        return slots

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # the session should begin with a `session_started` event

        events = [SessionStarted()]

        # any slots that should be carried over should come after the
        # `session_started` event
        events.extend(self.fetch_slots(tracker))

        # an `action_listen` should be added at the end as a user message follows
        events.append(ActionExecuted("utter_greet"))

        return events


        #Tracker.get_intent_of_latest_message