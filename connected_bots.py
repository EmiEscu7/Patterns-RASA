import requests
import json
import time
import queue

class Bot():

    def __init__(self, name, port, mediator):
        self.name = name
        self.port = port  
        self.url =  'http://localhost:'+str(port)+'/webhooks/rest/webhook'
        self.mediator = mediator
        if(name != "Scrum Master"):
            self.__instance_chatbot()

    def get_name(self):
        return self.name
    
    def get_port(self):
        return self.port

    def get_url(self):
        return self.url

    def __eq__(self, other):
        return ((self.get_name() == other.get_name())  and (self.get_port() == other.get_port()))
    
    def __instance_chatbot(self):
        #seteo el nombre de mi bot!!
       #url = self.get_url()
        data = {"sender": self.get_name(), "message": "Hola "+self.get_name()}
        x = requests.post(self.get_url(), json = data)
        #print(x.json())
        #if(json.load(x.json())['text'] == 'Bot Activado'):
        #    return True
        #return False
    
    def send_message(self, msg, rol, other=None):
        if(rol == 'Respondeme' and self.get_name() != "Scrum Master"):
            data = {"sender":self.get_name(), "message": msg}
        elif (self.get_name() == "Scrum Master"):
            data = {"sender":other.get_name(), "message": msg}
        else:
            data = {"sender":'Escucha', "message": msg}
        x = requests.post(self.get_url(), json = data)
        rta = x.json()
        text = ""
        for entry in rta:
            text += entry['text']
        
        if x.status_code == 200:
            return text
        else:
            print(x.raw)
            return None
    
    def notifyAll(self, msg, destino):
        mediator.notifyAll(self,msg,destino)



class Mediator():
    def __init__(self,name,scrum=None,developers=None):
        self.name = name
        self.scrum = scrum #lista de los Scrum's Masters
        self.developers = developers #Lista de los developers

    def set_developers(self, devs):
        self.developers = devs

    def set_scrum(self, scrums):
        self.scrum = scrums

    def notifyAll(self,origen, message, destino):
        answer_queue = [] #lista de las rta's que recibe el mediator
        for sc in self.scrum:
            if(sc == destino):
                rta = sc.send_message(message,'Respondeme', other=origen)
                if(rta != ''):
                    answer_queue.append([rta,sc])
                else:
                    print("-----> El SM:" + sc.get_name() +"que le tocaba responder dijo vacio <-----")
            elif(sc != origen):
                rta = sc.send_message(message,'Escucha', other=origen)
                if(rta != ''):
                    answer_queue.insert(0,[rta,sc])

        for dev in self.developers: #recorre la lista dev y les pide que genern una rta al message
            if(dev == destino):
                rta = dev.send_message(message,'Respondeme')
                if(rta == ''):
                    print("-----> El DEV: " + dev.get_name() + " que le tocaba responder dijo vacio <-----")
                else:
                    answer_queue.append([rta,dev])
                
                #esto es una "interrupcion"
            elif(dev != origen):  
                rta = dev.send_message(message,'Escucha')
                if(rta != ''):
                    answer_queue.insert(0,[rta,dev])
                else:
                    print(dev.get_name() + ": " + rta)

            
        #en este punto en la answer_queue tenes todas las respuestas a 'message'

        while (len(answer_queue) != 0): #ahora recorremos la lista de rtas enviando todo al que origino
            variable = answer_queue.pop(0) #la invocacion del notifyAll
            print(variable[1].get_name() + ": " + variable[0])
            self.notifyAll(variable[1],variable[0], origen)          
            #si el mensaje es chau, no llamo a recursion
            #esto corta cuando se vacia la queue o todos lanzan ''. Para que lancen '' los dev's cuando
            #hay una interrupción, luego del agradecimiento que dispare un action_listen entonces no se
            #agregaria nada a queue
            
            #para mentirle a rasa: si en la cola tenes mas de un elemento es porque tenes una "interrupcion"
            #osea te respondio uno que tenia que 'Escuchar' por lo tanto a Rasa le podes mentir diciendole
            #al segundo bot "Hubo una interrumcion" o algo por el estilo y que él internamente resuelva
            #eso y se plantee la nueva pregunta que va a hacerle. Ejemplo: esta hablando Emi - Scrum, Emi dice
            #tuve un problema entonces por casualidad un DEV dice 'Resolvelo así..' y al mismo tiempo el Scrum
            #dice algo como 'Que pena...', en la cola tenes 2 elementos, lanzas primero el del DEV
            #para que siga ese hilo conversacional el dev con Emi (gracias por la ayuda bla bla bla)
            #y al ser recursivo cuando esto vuelva va a seguir teniendo un elemento la queue, el mensaje del SC
            #entonces si vos invertis el mensaje, es decir ahora se lo mandas al Scrum en vez a Emi pero con
            #una especie de clave o algo por el estilo le estas avisando al SC que hubo una "interrupcion"
            #en su conversacion, por lo que su logica interna resolverá que hacer, si preguntar otra cosa o lo q se le cante

            if(len(answer_queue) == 1): #es decir queda un solo bot, el SM. Esto es para que retome la conversacion
                scrum_master = answer_queue.pop(0)##un paso más adelante de como habia quedado tras la interrupcion
                rta = scrum_master[1].send_message(scrum_master[0], "Respondeme")
                #answer_queue.append([rta,scrum_master[0]])
                scrum_master[1].notifyAll(rta, self, scrum_master[0]) #entro en recurrencia al notifyAll del SM


mediator = Mediator("mediator")

emi = Bot("Emiliano", 5005, mediator)
matiB = Bot("MatiasB", 5006, mediator)
sm = Bot("Scrum Master", 5007, mediator)
pedro = Bot("Pedro", 5008, mediator)

mediator.set_developers([emi,matiB,pedro])
mediator.set_scrum([sm])

sm.notifyAll("Con que trabajaste el dia de ayer?",pedro)

#escuchador = Bot("Escucha", 1111)
# Puertos donde tienen que estar corriendo los dos chatbots

#port_EMI = 5005
#port_MATI = 5006
#port_PEDRO = 5008
#port_SM = 5007

# Tiempo de espera entre mensaje y mensaje para que no vaya a las chapas (en segundos)
delay = 0.5

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