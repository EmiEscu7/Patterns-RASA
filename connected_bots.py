import requests
import time


def send_message(port, message, sender):
    """
    Esta función manda un mensaje a un chatbot corriendo en local host y imprime el mensaje recibido (tmb lo devuelve si lo queres usar para algo)
    Parametros:
        port -> numero de puerto donde corre el chatbot (int)
        message -> mensaje que se le quiere enviar (string)
        sender -> identificador de quien lo envia (string)	

    Devuelve:
        string con el texto del mensaje si esta todo ok
        None si tiro error
    """
    #ESTO LO AGREGO YO A VER SI FUNCA
    url = 'http://localhost:'+str(port)+'/webhooks/rest/webhook'
    data = {"sender": sender, "message": message}

    #cambie el parametro que pasan, en vez de data lo paso por json
    x = requests.post(url, json = data)

    print(sender + ": " + x.text)

    if x.status_code == 200:
        return x.text
    else:
        print(x.raw)
        return None

# Puertos donde tienen que estar corriendo los dos chatbots
port_c1 = 5005
port_c2 = 5006

# Tiempo de espera entre mensaje y mensaje para que no vaya a las chapas (en segundos)
delay = 0.5


# Mando el mensaje inicial simulando que soy el chatbot 1
message_c1 = send_message(port_c1, "Hello", "Chatbot 1")

# Loop infinito de los chatbots mandandose mensajes entre si, la conversacion se imprime en consola desde la funcion send_message
while True:
    message_c2 = send_message(port_c2, message_c1, "Chatbot 2")
    time.sleep(delay)
    message_c1 = send_message(port_c1, message_c2, "Chatbot 1")
    time.sleep(delay)
