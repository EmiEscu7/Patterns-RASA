import requests
import json
import time
import queue

class Bot():

    def __init__(self, name, port, mediator):
        self.name = name
        self.port = port  
        self.url =  'http://localhost:'+str(port)+'/webhooks/rest_custom/webhook'
        self.mediator = mediator
        if(name != "Scrum Master"):
            self.__instance_chatbot()

    def __str__(self):
        return str(self.name)
        
    def get_name(self):
        return self.name
    
    def get_port(self):
        return self.port

    def get_url(self):
        return self.url

    def __eq__(self, other):
        return ((self.get_name() == other.get_name())  and (self.get_port() == other.get_port()))
    
    def __hash__(self):
        return hash(self.__key())
    
    def __key(self):
        return self.name

    def __instance_chatbot(self):
        #El objetivo de este metodo es instanciar los slots del bot RASA
        data = {"sender": self.get_name(), "message": "Hola "+ self.get_name(), "metadata": { "flag": 1 , "toMe": 1}}
        x = requests.post(self.get_url(), json = data)
 
    def send_message(self, msg, sender, flag=1, toMe=1):
        """
        msg = mensaje a enviar
        sender = quien envia el mensaje
        Flag = 0 -> No responde (porque interpreta como que no es el ultimo mensaje que debe recibir)
        Flag = 1 -> Responde (porque interpreta la politica que es el ultimo mensaje que debe recibir)
        toMe = 1 -> Soy el destino interpretan los bots
        toMe = 0 -> No soy el destino interpretan los bots
        """
        data = {"sender": sender.get_name(), "message": msg, "metadata": { "flag": flag, "toMe": toMe} }
        x = requests.post(self.get_url(), json = data)
        rta = x.json()
        text = ""
        if(rta != [] ):
            while(len(rta) > 1): #Lo ultimo que hay en rta es el nombre a quien está destinado el mensaje
                text += rta.pop(0)['text'] + ". "
            text = [text]
            text.append(rta.pop(0)['text'])
        else:
            text = ['','None']
        if x.status_code == 200:
            return text
        else:
            print(x.raw)
            return None
    
    def notifyAll(self, msg, destino):
        mediator.notifyAll(self,msg,destino)

    def notifyAllMeeting(self,msg,dev):
        for d in dev:
            mediator.notifyAll(self,msg,d)
 
 

class Mediator():
    def __init__(self,name,scrum=None,developers=None):
        self.name = name
        self.scrum = scrum #lista de los Scrum's Masters
        self.developers = developers #Lista de los developers

    def set_developers(self, devs):
        self.developers = devs

    def set_scrum(self, scrums):
        self.scrum = scrums

    
    def notifyAll(self,origen:Bot, message, destino:Bot):
        answer_queue = [] #lista de las rta's que recibe el mediator
        metiches = {} #un Dict {key= dev, value= [rta,a quien le respondio eso]}
        for sc in self.scrum:
            if(sc != origen):
                if(sc == destino):
                    rta = sc.send_message(message, origen, toMe=1)
                    if (rta[0] != ''): #rta = [message,sender]
                        answer_queue.append([sc, rta[0]])                 
                else:
                    rta = sc.send_message(message, origen, toMe=0)
                    if(rta[0] != ''):#alguien que no tenia que responder, respondio
                        metiches[sc] = rta
                        answer_queue.append([sc, rta[0]])                 
            
        for dev in self.developers: #recorre la lista dev y les pide que genern una rta al message
            if(dev != origen):
                if(dev == destino):
                    rta = dev.send_message(message, origen, toMe=1)
                    if(rta[0] != ''):
                        answer_queue.append([dev, rta[0]])
                else:   
                    rta = dev.send_message(message, origen, toMe=0)
                    if(rta[0] != ''):#alguien que no tenia que responder, respondio
                        metiches[dev] = rta #{key= dev, value= [rta,a quien le respondio eso]}
                        answer_queue.append([dev, rta[0]])
                
  
        #en este punto en la answer_queue tenes todas las respuestas a 'message'
        #print("---A fines de control imprimo la lista de answer---")
        #print(answer_queue)
        
        while (len(answer_queue) > 1): 
            """
            ahora recorremos la lista de respuestas enviando todo al que origino
            la invocacion del notifyAll
            """
            prox_sms = answer_queue.pop(0)  # prox_sms = [dev/scrum,rta]
            print(prox_sms[0].get_name() + ": " + prox_sms[1])
            answer_dev = origen.send_message(prox_sms[1], prox_sms[0], flag=0, toMe= 1) #Con flag en 0 para que no responda el bot
        
        if(len(answer_queue) == 1):
            prox_sms = answer_queue.pop(0)  # prox_sms = [dev/scrum,rta]
            print(prox_sms[0].get_name() + ": " + prox_sms[1])
            answer_dev = origen.send_message(prox_sms[1], prox_sms[0], flag=1, toMe= 1) 
            #answer_dev '[{"recipient_id":"Emiliano","text":"Que onda perri, soy Emiliano"},
            #             {"recipient_id":"Emiliano","text":"sended to"}]'
            #esto pasa 1° por el send_message que lo limpia y lo deja como:
            #answer_dev = ["Que onda perri, soy Emiliano", "sended to"]
            #Por lo tanto en en answer_dev[0] tenemos el mensaje que respondió el bot y va dirigido hacia 
            # answer_dev[1] = sended to
            
            bot = self.give_me_bot(answer_dev[1])
            print(str(origen.get_name()) + ": " + str(bot.get_name()) + ", " + answer_dev[0])
            if(bot in metiches.keys() and bot != destino):
                self.notifyAll(bot, metiches[bot], origen) 
            else:
                self.notifyAll(origen, answer_dev[0], bot)
                
    def give_me_bot(self,name):
        #Retorna el objeto BOT asociado a name
        for dev in self.developers:
            if(dev.get_name() == name):
                return dev
        for sc in self.scrum:
            if(sc.get_name() == name):
                return sc


# Tiempo de espera entre mensaje y mensaje para que no vaya a las chapas (en segundos)
delay = 0.5
mediator = Mediator("mediator")
# Puertos donde tienen que estar corriendo los dos chatbots
#port_EMI = 5005
#port_MATI = 5006
#port_PEDRO = 5008
#port_SM = 5007
emi = Bot("Emiliano", 5005, mediator)
matiB = Bot("MatiasB", 5006, mediator)
sm = Bot("MatiasG", 5007, mediator)
pedro = Bot("Pedro", 5008, mediator)

mediator.set_developers([emi,matiB,pedro])
mediator.set_scrum([sm])

sm.notifyAll("Con que trabajaste el dia de ayer?",pedro)
#sm.notifyAllMeeting("Con que trabajaste ayer?",[pedro,emi,matiB])


"""
esto corta cuando se vacia la queue o todos lanzan ''. Para que lancen '' los dev's cuando
hay una interrupción, luego del agradecimiento que dispare un action_listen entonces no se
agregaria nada a queue

para mentirle a rasa: si en la cola tenes mas de un elemento es porque tenes una "interrupcion"
osea te respondio uno que tenia que 'Escuchar' por lo tanto a Rasa le podes mentir diciendole
al segundo bot "Hubo una interrumcion" o algo por el estilo y que él internamente resuelva
eso y se plantee la nueva pregunta que va a hacerle. Ejemplo: esta hablando Emi - Scrum, Emi dice
tuve un problema entonces por casualidad un DEV dice 'Resolvelo así..' y al mismo tiempo el Scrum
dice algo como 'Que pena...', en la cola tenes 2 elementos, lanzas primero el del DEV
para que siga ese hilo conversacional el dev con Emi (gracias por la ayuda bla bla bla)
y al ser recursivo cuando esto vuelva va a seguir teniendo un elemento la queue, el mensaje del SC
entonces si vos invertis el mensaje, es decir ahora se lo mandas al Scrum en vez a Emi pero con
una especie de clave o algo por el estilo le estas avisando al SC que hubo una "interrupcion"
en su conversacion, por lo que su logica interna resolverá que hacer, si preguntar otra cosa o lo q se le cante


Codigo viejo:
scrum_master = answer_queue.pop(0)##un paso más adelante de como habia quedado tras la interrupcion
rta = scrum_master[1].send_message(scrum_master[0], "Respondeme")
#answer_queue.append([rta,scrum_master[0]])
scrum_master[1].notifyAll(rta, self, scrum_master[0]) #entro en recurrencia al notifyAll del SM
"""
# Mando el mensaje inicial simulando que soy el chatbot 1
#print("Scrum Master: Buenas")
#actual_dev = [emi, escuchador, escuchador]
#actual_dev_name = emi.get_name()
#puerto destino, msj a enviar, chatbot destino
#message_c1 tiene la respuesta del send_message
#message_emi = send_message("Buenas Emiliano", emi, emi)  #Chatbot Emiliano
#message_mati = send_message("Buenas MatiasB", matiB, matiB)  #Chatbot MatiasB
#message_pedro = send_message("Buenas Pedro", pedro, pedro)  #Chatbot Pedro
#print(message_emi)
#print(message_mati)
"""
lista_msg = [message_emi, message_mati, message_pedro]
msg_to_send = lista_msg.pop(0)

adios = ["Hasta mañana, que le vaya bien", "Hasta la proxima, que vaya bien",
        "hasta mañana","chau,hasta luego","buenas noches","adios","hasta la proxima","que tengas un buen dia",
        "nos vemos luego","chau chau", "nv bro","Nos vemos mañana","Nos re vimos mañana","Nos re vimos perrito" ]

# Loop infinito de los chatbots mandandose mensajes entre si, la conversacion se imprime en consola desde la funcion send_message
while True:
    if(not msg_to_send in adios):
        message_sm = send_message(msg_to_send, sm, sm)
        time.sleep(delay)
        message_emi = send_message(message_sm, actual_dev[0], emi)
        message_mati = send_message(message_sm, actual_dev[1], matiB)
        message_pedro = send_message(message_sm, actual_dev[2], pedro)
        #Si emi es el primero que esta hablando, Mati no va a responder hasta que Emi se despida
        #Cuando Emi se despide, se hace el pop de la lista de mensajes
        #y queda el primer mensaje que mati envio para continuar la conversacion con el
        #verificar con quien habla y cambiar el msg_to_send
        if(actual_dev[0].equals(emi)):
            msg_to_send = message_emi
        elif (actual_dev[1].equals(matiB)):
            msg_to_send = message_mati
        else:
            msg_to_send = message_pedro
    else:
        if (len(lista_msg) == 2): 
            msg_to_send = lista_msg.pop(0)
            actual_dev[0] = escuchador
            actual_dev[1] = matiB
        elif (len(lista_msg) == 1):
            msg_to_send = lista_msg.pop(0)
            actual_dev[1] = escuchador
            actual_dev[2] = pedro
        else:
            break
    

"""