from rasa.core.channels.channel import InputChannel
from rasa.core.channels.rest import RestInput


class CustomConnector(InputChannel):
    def name() -> Text:
        """Name of your custom channel."""
        return "customconnector"
    
