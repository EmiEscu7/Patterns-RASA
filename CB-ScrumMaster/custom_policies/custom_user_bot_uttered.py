from typing import (
    List,
    Dict,
    Text,
    Any,
    Optional
)
from rasa.shared.core.events import Event, UserUttered


class UserBotUttered():
    def __init__(self,
        last_message:UserUttered,
        bot_predict_event:Optional[Text]
    ) -> None:
        """
            Crea un evento que contiene el mensaje que recibio el bot
            y el evento que predice el bot para dicho mensaje
        """
        self.message_user = last_message
        self.bot_predict_event = bot_predict_event
    
    def get_message_user(self) -> UserUttered:
        return self.message_user

    def get_bot_predict(self) -> Text:
        return self.bot_predict_event

    def set_bot_predict(self, bot_predict):
        self.bot_predict_event = bot_predict