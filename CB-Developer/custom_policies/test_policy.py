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
from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY
from rasa_sdk.events import SlotSet


logger = logging.getLogger(__name__)

# temporary constants to support back compatibility
MAX_HISTORY_NOT_SET = -1
OLD_DEFAULT_MAX_HISTORY = 5

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

        #name = training_trackers.get_slot('name')
        #print(name)

        pass

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> PolicyPrediction:
        

        name = tracker.get_slot('name')
        print("ESTE ES EL NAME QUE ENTRO A LA POLICY: " + name)
        with open("personalities.json", "r") as file:
            personality = json.load(file)[name]

        vectorP = []
        for key, value in personality.items():
            vectorP.append(value)

        pesos = [0.35,0.4,0.1,0.05,0.3]

        relation = float(0.0)
        for i in range(4):
            relation += vectorP[i] * pesos[i]

        res = [ [float(0.3), "_formal"], 
                [float(0.6), "_comun"], 
                [float(1.0), "_informal"] ]
       
        rta = 'utter_'
        intent = tracker.latest_message.intent.get(INTENT_NAME_KEY)
        rta += intent
        i = 0 
        while (relation > res[i][0]):
            i+=1
        rta += res[i][1]
        tipoRta = res[i][1]
        
        result = self._default_predictions(domain)



       # sender_id = tracker.sender_id
       # print("sender ID =" + sender_id2)
       # latest = tracker.latest_message.get('text')
       # print("latest: "+ latest)
       #intent = tracker.latest_message.intent.get(INTENT_NAME_KEY)
       #and intent == 'presentation_user'):
        sender_id = tracker.current_state()['sender_id']
        #nombrev2 = tracker.current_state()['name']
        #print("----> nombrev2" + nombrev2)
        print("---------------------> SENDER:"+ sender_id)
        print("---------------------> NOMBRE:"+ name)
        
        if (sender_id != 'Escucha'):
            if(not self.answered): 
                if (intent == 'doYouHaveProblem'):
                    prox = 'action_tipo' + tipoRta
                    result = confidence_scores_for(prox,1.0,domain)
                elif(intent == 'agradecimiento'):
                    result = confidence_scores_for('action_listen', 1.0, domain)
                else:    
                    result = confidence_scores_for(rta, 1.0, domain)
                self.answered = True
            else:
                self.answered = False
        else:
            result = confidence_scores_for('action_listen', 1.0, domain)
            self.answered = True

        return self._prediction(result)

    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "test_policy.json"


    #def obtenerResultado()
        ##agarro el nombre de la persona con la que estoy hablando para saber como responderle
