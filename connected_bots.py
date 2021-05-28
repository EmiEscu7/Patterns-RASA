import requests
import json
import time


class Developer():

    def __init__(self, name, port):
        self.name = name
        self.port = port   

    def get_name(self):
        return self.name
    
    def get_port(self):
        return self.port

    def equals(self, other):
        return ((self.get_name() == other.get_name())  and (self.get_port() == other.get_port()))


def send_message(message, developer, portDestino):
    """
    Esta función manda un mensaje a un chatbot corriendo en local host y imprime el mensaje recibido (tmb lo devuelve si lo queres usar para algo)
    Parametros:
        port -> numero de puerto donde corre el chatbot (int) Puerto de destino
        message -> mensaje que se le quiere enviar (string) Mensaje que se envia
        sender -> identificador de quien lo envia (string)	Nombre del receptor

    Devuelve:
        string con el texto del mensaje si esta todo ok
        None si tiro error
    """
    #ESTO LO AGREGO YO A VER SI FUNCA
    url = 'http://localhost:'+str(portDestino)+'/webhooks/rest/webhook'
    data = {"sender": developer.get_name(), "message": message}
    #print(developer.get_name())
    #cambie el parametro que pasan, en vez de data lo paso por json
    x = requests.post(url, json = data)
    rta = x.json()
    text = ""
    for entry in rta:
        text += entry['text']
    #text = rta[0]['text']
    if((developer.get_port() == portDestino) or (5007 == portDestino)):
        print(developer.get_name() + ": " + text)

    if x.status_code == 200:
        return text
    else:
        print(x.raw)
        return None


emi = Developer("Emiliano", 5005)
matiB = Developer("MatiasB", 5006)
sm = Developer("Scrum Master", 5007)
pedro = Developer("Pedro", 5008)
# Puertos donde tienen que estar corriendo los dos chatbots

#port_EMI = 5005
#port_MATI = 5006
#port_PEDRO = 5008
#port_SM = 5007




# Tiempo de espera entre mensaje y mensaje para que no vaya a las chapas (en segundos)
delay = 0.5

# Mando el mensaje inicial simulando que soy el chatbot 1
print("Scrum Master: Buenas")
actual_dev = emi
#actual_dev_name = emi.get_name()
#puerto destino, msj a enviar, chatbot destino
#message_c1 tiene la respuesta del send_message
message_emi = send_message("Buenas Emiliano", emi, emi.get_port())  #Chatbot Emiliano
message_mati = send_message("Buenas MatiasB", matiB, matiB.get_port())  #Chatbot MatiasB
message_pedro = send_message("Buenas Pedro", pedro, pedro.get_port())  #Chatbot Pedro
#print(message_emi)
#print(message_mati)

lista_msg = [message_emi, message_mati, message_pedro]
msg_to_send = lista_msg.pop(0)

adios = ["Hasta mañana, que le vaya bien", "Hasta la proxima, que vaya bien",
        "hasta mañana","chau,hasta luego","buenas noches","adios","hasta la proxima","que tengas un buen dia",
        "nos vemos luego","chau chau", "nv bro","Nos vemos mañana","Nos re vimos mañana","Nos re vimos perrito" ]

# Loop infinito de los chatbots mandandose mensajes entre si, la conversacion se imprime en consola desde la funcion send_message
while True:
    if(not msg_to_send in adios):
        message_sm = send_message(msg_to_send, sm, sm.get_port())
        time.sleep(delay)
        message_emi = send_message(message_sm, actual_dev, emi.get_port())
        message_mati = send_message(message_sm, actual_dev, matiB.get_port())
        message_pedro = send_message(message_sm, actual_dev, pedro.get_port())
        #Si emi es el primero que esta hablando, Mati no va a responder hasta que Emi se despida
        #Cuando Emi se despide, se hace el pop de la lista de mensajes
        #y queda el primer mensaje que mati envio para continuar la conversacion con el
        #verificar con quien habla y cambiar el msg_to_send
        if(actual_dev.equals(emi)):
            msg_to_send = message_emi
        elif (actual_dev.equals(matiB)):
            msg_to_send = message_mati
        else:
            msg_to_send = message_pedro
    else:
        if (len(lista_msg) == 2): 
            msg_to_send = lista_msg.pop(0)
            actual_dev = matiB
        elif (len(lista_msg) == 1):
            msg_to_send = lista_msg.pop(0)
            actual_dev = pedro
        else:
            break
    

