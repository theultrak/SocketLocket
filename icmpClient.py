from socket import *
#Hi this is a push attempt
def openSocket():
    try:
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        print("Socket Open")
    except PermissionError as e:
        print(f"Error: {e}. Run with admin access.")
        exit()

def packetConstruction():
    print("Constructing packet")

def pingSend():
    print("Pinging processes beginning")

openSocket()
packetConstruction()
pingSend()
