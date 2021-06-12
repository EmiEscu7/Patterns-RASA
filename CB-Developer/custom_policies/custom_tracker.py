import contextlib
import itertools
import json
import logging
import os
import pickle
from datetime import datetime, timezone
from collections import deque
from time import sleep
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Text,
    Union,
    TYPE_CHECKING,
)
from rasa.shared.core.events import BotUttered, Event, UserUttered
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.slots import Slot

class CustomTracker(DialogueStateTracker):

    def __init__(
        self,
        sender_id: Text,
        slots: Optional[Iterable[Slot]],
        max_event_history: Optional[int] = None,
        sender_source: Optional[Text] = None,
        is_rule_tracker: bool = False,
        ) -> None:
        #Initialize the custom-tracker like the super
        super().__init__(
                     sender_id,
                     slots,
                     max_event_history,
                     sender_source,
                     is_rule_tracker
                )

        
    def add_events(self, evts: Deque[Event]):
        self.events.extend(evts)    
       
    def set_slot(self, key: Text, value: Any) -> None:
        super()._set_slot(key, value)

    def set_paused(self,value):
        self._paused = value

    def set_followup_action(self,action):
        self.followup_action = action

    def set_latest_action(self,action):
        self.latest_action = action

    def set_latest_message(self, msg: Optional[UserUttered]):
        self.latest_message = msg

    def set_latest_bot_utterance(self, utt: Optional[BotUttered]):
        self.latest_bot_utterance = utt

    def set_active_loop(self,loop_name: Optional[Text]):
        super().change_loop_to(loop_name)

    def get_latest_entity_values(self,
        entity_type: Text,
        entity_role: Optional[Text] = None,
        entity_group: Optional[Text] = None,
    ) -> Iterator[Text]:
        return super().get_latest_entity_values(entity_type)

    def update_tracker(self, tracker: DialogueStateTracker) -> None:
        self.set_active_loop(tracker.active_loop)
        self.set_followup_action(tracker.followup_action)
        self.set_latest_action(tracker.latest_action)
        self.set_latest_bot_utterance(tracker.latest_bot_utterance) 
        self.set_latest_message(tracker.latest_message)
        self.set_paused(tracker._paused)
        self.add_events(tracker.events)
