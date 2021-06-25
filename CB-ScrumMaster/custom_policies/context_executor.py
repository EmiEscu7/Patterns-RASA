import random as rd


class IContextExecutor():

    def __init__(self):
        pass

    def decide_next(self, message):
        """
            This method will decide the next answer
            Depending on the type of context executor
            message:
                - In the first position (index = 0) the message is found
                - In the second position (index = 1) the intent is found
                - In the third position (index = 2) the utter/action (answer) is found
        """
        pass


class ContextExecutorGoodPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, message):
        """
            This method represent the behaviour of a good person.
        """

        rtas = []
        for sender in message.keys():
            rtas.append(message[sender][2]) #le responde a todos
        
        return rtas


class ContextExecutorNormalPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, message):
        """
            This method represent the behaviour of a normal person.
        """

        rtas = []
        for sender in message.keys():
            ult_sender = sender

        rtas.append(message[ult_sender][2]) #Le respone a la ultima persona que le mando un msj
        
        return rtas


class ContextExecutorBadPerson(IContextExecutor):

    def __init__(self):
        self.super().__init__()

    
    def decide_next(self, message):
        """
            This method represent the behaviour of a bad person.
        """

        rtas = []
        the_chosen_one = rd.randint(0, (len(message)-1))
        i = 0
        senders = message.keys()
        for i in range(the_chosen_one + 1):
            ult_sender = senders[i]

        rtas.append(message[ult_sender][2]) #Le respone a una persona al azar. Porque le gusta generar quilombo
        
        return rtas
        
