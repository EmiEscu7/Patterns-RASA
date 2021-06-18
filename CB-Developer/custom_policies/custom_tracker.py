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
from rasa.shared.core.trackers import EventVerbosity
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
from rasa.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_VALUE,
    ENTITY_ATTRIBUTE_TYPE,
    ENTITY_ATTRIBUTE_GROUP,
    ENTITY_ATTRIBUTE_ROLE,
    ACTION_TEXT,
    ACTION_NAME,
    ENTITIES,
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
        self.latest_message = []
        
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

    def add_latest_message(self, msg: Optional[UserUttered]):
        self.latest_message.append(msg)
    
    def get_latest_message(self) -> UserUttered:
        if(len(self.latest_message) > 0):
            return self.latest_message[-1]
        else:
            return UserUttered(None)
            
    def set_latest_bot_utterance(self, utt: Optional[BotUttered]):
        self.latest_bot_utterance = utt

    def set_active_loop(self,loop_name: Optional[Text]):
        self._change_loop_to(loop_name)
    def _change_loop_to(self, loop_name: Optional[Text]) -> None:
        """Set the currently active loop.
        Args:
            loop_name: The name of loop which should be marked as active.
        """
        if loop_name is not None:
            self.active_loop = {
                LOOP_NAME: loop_name,
                LOOP_INTERRUPTED: False,
                LOOP_REJECTED: False,
                TRIGGER_MESSAGE: self.get_latest_message().parse_data,
            }
        else:
            self.active_loop = {}

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
        self.add_latest_message(tracker.latest_message)
        self.set_paused(tracker._paused)
        self.add_events(tracker.events)


    #Metodos que deben ser redefinidos al usar a latest_message como una lista
    def current_state(
        self, event_verbosity: EventVerbosity = EventVerbosity.NONE
    ) -> Dict[Text, Any]:
        """Returns the current tracker state as an object."""
        _events = self._events_for_verbosity(event_verbosity)
        if _events:
            _events = [e.as_dict() for e in _events]
        latest_event_time = None
        if len(self.events) > 0:
            latest_event_time = self.events[-1].timestamp

        return {
            "sender_id": self.sender_id,
            "slots": self.current_slot_values(),
            "latest_message": self._latest_message_data(),
            "latest_event_time": latest_event_time,
            FOLLOWUP_ACTION: self.followup_action,
            "paused": self.is_paused(),
            "events": _events,
            "latest_input_channel": self.get_latest_input_channel(),
            ACTIVE_LOOP: self.active_loop,
            "latest_action": self.latest_action,
            "latest_action_name": self.latest_action_name,
        }

    def _latest_message_data(self) -> Dict[Text, Any]:
        parse_data_with_nlu_state = self.get_latest_message().parse_data.copy()
        # Combine entities predicted by NLU with entities predicted by policies so that
        # users can access them together via `latest_message` (e.g. in custom actions)
        parse_data_with_nlu_state["entities"] = self.get_latest_message().entities

        return parse_data_with_nlu_state

    def change_loop_to(self, loop_name: Optional[Text]) -> None:
        """Set the currently active loop.
        Args:
            loop_name: The name of loop which should be marked as active.
        """
        if loop_name is not None:
            self.active_loop = {
                LOOP_NAME: loop_name,
                LOOP_INTERRUPTED: False,
                LOOP_REJECTED: False,
                TRIGGER_MESSAGE: self.get_latest_message().parse_data,
            }
        else:
            self.active_loop = {}

    def get_latest_entity_values(
        self,
        entity_type: Text,
        entity_role: Optional[Text] = None,
        entity_group: Optional[Text] = None,
    ) -> Iterator[Text]:
        """Get entity values found for the passed entity type and optional role and
        group in latest message.
        If you are only interested in the first entity of a given type use
        `next(tracker.get_latest_entity_values("my_entity_name"), None)`.
        If no entity is found `None` is the default result.
        Args:
            entity_type: the entity type of interest
            entity_role: optional entity role of interest
            entity_group: optional entity group of interest
        Returns:
            Entity values.
        """

        return (
            x.get(ENTITY_ATTRIBUTE_VALUE)
            for x in self.get_latest_message().entities
            if x.get(ENTITY_ATTRIBUTE_TYPE) == entity_type
            and x.get(ENTITY_ATTRIBUTE_GROUP) == entity_group
            and x.get(ENTITY_ATTRIBUTE_ROLE) == entity_role
        )

    def _reset(self) -> None:
        """Reset tracker to initial state - doesn't delete events though!."""

        self._reset_slots()
        self._paused = False
        self.latest_action = {}
        self.latest_message = [] #clear a list in python
        self.latest_bot_utterance = BotUttered.empty()
        self.followup_action = ACTION_LISTEN_NAME
        self.active_loop = {}

    #Metodo añadido para actualizar el Tracker que utiliza RASA
    def get_latest_event(self) -> Event: 
        return self.events[-1]