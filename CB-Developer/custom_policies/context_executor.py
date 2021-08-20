import random as rd


class IContextExecutor():

    def __init__(self):
        self.answers = ['utter_send_destination', 'action_listen']
        #pass

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
        IContextExecutor.__init__(self)

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a good person.
            Currently, this bot answer everyone.
        """
        rtas = self.answers.copy()
        destinies = []
        for sender in messages.keys():
            rtas.insert(0, messages[sender].get_bot_predict())         
            destinies.insert(0, sender)
        print("RESPUESTAS ---> " + str(rtas))
        return [rtas, destinies] #rtas y destino. 


class ContextExecutorNormalPerson(IContextExecutor):

    def __init__(self):
        IContextExecutor.__init__(self)

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a normal person.
            The bot that is normal, responds the last message that recieve
        """

        the_chosen_one = list(messages.keys())[-1]
        rtas = self.answers.copy()
        rtas.insert(0, messages[the_chosen_one].get_bot_predict()) 
        print("RESPUESTAS ---> " + str(rtas))
        return [rtas, the_chosen_one]


class ContextExecutorBadPerson(IContextExecutor):

    def __init__(self):
        IContextExecutor.__init__(self)

    
    def decide_next(self, messages):
        """
            This method represent the behaviour of a bad person.
            Choose random message
        """

        random_select = rd.randint(0, (len(messages)-1))
        i = 0
        senders = list(messages.keys())
        the_chosen_one = senders[random_select]
        rtas = self.answers.copy()
        rtas.insert(0, messages[the_chosen_one].get_bot_predict()) #Le respone a una persona al azar. Porque le gusta generar quilombo
        print("RESPUESTAS ---> " + str(rtas))
        return [rtas, the_chosen_one]