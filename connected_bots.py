import requests
import json
import time


def send_message(port, message, sender):
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
    url = 'http://localhost:'+str(port)+'/webhooks/rest/webhook'
    data = {"sender": sender, "message": message}

    #cambie el parametro que pasan, en vez de data lo paso por json
    x = requests.post(url, json = data)
    rta = x.json()
    text = ""
    for entry in rta:
        text += entry['text']
    #text = rta[0]['text']
    print(sender + ": " + text)

    if x.status_code == 200:
        return text
    else:
        print(x.raw)
        return None

# Puertos donde tienen que estar corriendo los dos chatbots
port_D = 5005
port_SM = 5006

# Tiempo de espera entre mensaje y mensaje para que no vaya a las chapas (en segundos)
delay = 0.5


# Mando el mensaje inicial simulando que soy el chatbot 1
print("Developer: Hola soy Emiliano")
#puerto destino, msj a enviar, chatbot destino
message_c1 = send_message(port_SM, "Hola soy Emiliano", "Scrum Master")

# Loop infinito de los chatbots mandandose mensajes entre si, la conversacion se imprime en consola desde la funcion send_message
while True:
    message_c2 = send_message(port_D, message_c1, "Developer")
    time.sleep(delay)
    message_c1 = send_message(port_SM, message_c2, "Scrum Master")
    time.sleep(delay)
