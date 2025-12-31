# Import necessary libraries for networking, threading, and system functions.
from socket import *
from threading import *
import time
import sys

# Global flag to signal threads to stop when the client exits.
global flagExit
flagExit = 0

# Create a UDP socket.
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Get server connection details from user input.
serverID = input("Please enter the server IP address: ")
serverPortStr = input("Please enter the server port number: ")
serverPort = int(serverPortStr)

print(f"Connecting to server at ({serverID},{serverPort})")

# Get the client's name and send it to the server.
clientName = input("Please enter your name: ")
clientSocket.sendto(clientName.encode(), (serverID, serverPort))

def receive(clientSocket):
    """Continuously receives and prints messages from the server."""
    global flagExit
    clientSocket.settimeout(3)

    while not flagExit:
        try:
            modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
            print(modifiedMessage.decode())
        except:
            # Continue on timeout to recheck the flag.
            continue

def sent(clientSocket):
    """Handles user input and sends messages to the server."""
    global flagExit
    while True:
        message = input("")
        if message.lower() == "exit":
            # Set flag and send exit message to close the program.
            flagExit = True
            clientSocket.sendto(message.encode(), (serverID, serverPort))
            break
        clientSocket.sendto(message.encode(), (serverID, serverPort))

# Create and start separate threads for sending and receiving.
t1 = Thread(target=receive, args=(clientSocket,))
t2 = Thread(target=sent, args=(clientSocket,))
t1.start()
t2.start()

# Wait for both threads to complete before the main program exits.
t1.join()
t2.join()