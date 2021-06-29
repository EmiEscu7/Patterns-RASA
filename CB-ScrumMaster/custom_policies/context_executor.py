import random as rd


class IContextExecutor():

    def __init__(self):
        self.answers = ['utter_send_destination', 'action-listen']
        pass

    def decide_next(self, messages):
        """
            This method will decide the next answer
            Depending on the type of context executor
            message args is a dict where the key is a sender and 
            the value is UserBotUttered object
        """
        pass


class ContextExecutorGoodPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a good person.
            Currently, this bot answer everyone.
        """
        destinies = []
        for sender in messages.keys():
            self.answers.insert(0, messages[sender].get_bot_predict())         
            self.destinies.insert(0, sender)
        return [self.answers, destinies] #rtas y destino. 


class ContextExecutorNormalPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a normal person.
            The bot that is normal, responds the last message that recieve
        """

        the_chosen_one = list(messages.keys())[-1]

        self.answers.insert(0, messages[the_chosen_one].get_bot_predict()) 
        
        return [self.answers, the_chosen_one]


class ContextExecutorBadPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a bad person.
            Choose random message
        """

        rtas = []
        random_select = rd.randint(0, (len(messages)))
        i = 0
        senders = messages.keys()
        the_chosen_one = senders[random_select]

        rtas.insert(0, messages[the_chosen_one].get_bot_predict()) #Le respone a una persona al azar. Porque le gusta generar quilombo
        
        return [rtas, the_chosen_one]