# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import json
import sys
import random as rd
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher



class ActionConsultEstado(Action):

    def name(self) -> Text:
        return "action_consultar_estado"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        nombre = tracker.get_slot('name')
        print(nombre)
        #numDev = int(rd.randint(1, 4))
        #dev = 'developer'+str(numDev)
        with open('tasks.json', 'r') as file:
            developer = json.load(file)[nombre] #Pedro{}

        name = developer['name']
        task = developer['currentTask']

        dispatcher.utter_message(text="Buenas {}. Cómo vas con {}?".format(name, task))

        return []
