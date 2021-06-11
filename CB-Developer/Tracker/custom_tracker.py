import contextlib
import itertools
import json
import logging
import os
import pickle
from datetime import datetime, timezone

from time import sleep
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Text,
    Union,
    TYPE_CHECKING,
)

from rasa.core.tracker_store


class CustomTracker():


    def __init__(
        self,
        domain: Optional[Domain],
        event_broker: Optional[EventBroken] = None,
        **kwargs: Dict[Text, Any]

    ) -> None:
        slef.super().__init__(domain, event_broker, kwargs)
        self.tracker_list = []

    
    def save(self, tracker: DialogueStateTracker) -> None:
        
