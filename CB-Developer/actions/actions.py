# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
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
class respuesta(Action):
    def name(self) -> Text:
        return "action_dar_respuesta"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        res = [ [float(0.2), "_yes"],
                [float(1.0), "_no"] ] 

        rta = "utter_my_problem"
        
        nro = random()
        print(nro)

        i = 0
        while(nro > res[i][0]):
            i+=1
        rta += res[i][1]
        
        ##rta += "_comun" ##acomodar esto porque siempre va a responder con comun 
        tipoRta = tracker.get_slot('tipoRta')
        print(tipoRta)
        rta += tipoRta
        dispatcher.utter_message(template = rta)
        return[]