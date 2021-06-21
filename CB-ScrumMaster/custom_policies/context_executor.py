


class ContexExecutor():

    def __init__(self, patienece):
        self.patienece = patienece
        self.interruptions = {} #dict que va a contener el bot como key, y la cantidad de interrupciones que hizo

    
    def there_is_interruption(self, bot) -> None:
        if(bot in self.interruptions):
            self.interruptions[bot] += 1
        else:
            self.interruptions[bot] = 1

    def exhausted(self):
        for bot, value in self.interruptions.items():
            if(not value < self.personality["paciencia"]):
                return [True, bot]
        return [False, None]

    def get_answer(self, answers, destiny):
        exh = self.exhausted
        rta_interurp = None
        if(exh[0]):
            rta_interurp = ["utter_do_not_interrupt", exh[1]]
            self.interruptions = {} #elimino todas las interrupciones. 
                                    #PODRIA SER QUE NO, YA QUE NORMALEMNTE ES ACUMULATIVO. 
                                    #PERO DE TESTEO ESTO VA BIEN
        #### DEVUELVO LA RTA QUE ME DIO EL BOT DESTINO
        rta_destiny = answers[destiny]
        return [rta_destiny, rta_interurp]
        
        
