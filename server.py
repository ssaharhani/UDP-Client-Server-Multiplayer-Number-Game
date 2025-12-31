from socket import *
from threading import *
import time
import os
import sys

global numberOfClient
numberOfClient = 0
clientCountLock = Lock()
clientList = []
global usedNumbers
usedNumbers = set()

# State Machine for the game
# 0: Initial Waiting (accepting new players)
# 1: In Round (submissions active, new players waiting)
# 2: Between Rounds (accepting new players)
# 3: Game Over (server shutting down)
global gameState
gameState = 0

global waitingList
waitingList = []
#----------------------------------------------------------------------------------------------------------------

# Server Connection Setup
serverName = "Main Game Server"
serverPort = 5012
serverSocket = socket(AF_INET, SOCK_DGRAM)
hostname = gethostname()
serverIP = gethostbyname(hostname)
serverSocket.bind((serverIP, serverPort))
print(f"\nThe game server started and listening on ({serverIP}, {serverPort})\n")

#----------------------------------------------------------------------------------------------------------------

# Displaying Messages
def broadcastMsg(message):
    global clientList, serverSocket
    for client in clientList:
        serverSocket.sendto(message.encode(), client['address'])

def displayMsg(message):
    print(message)

def oneClientMsg(message, clientAddress):
    try:
        serverSocket.sendto(message.encode(), clientAddress)
    except Exception as e:
        displayMsg(f"Error sending to {clientAddress}: {e}")
        displayMsg(f"Player {clientAddress} is likely disconnected and will be removed")
        with clientCountLock:
            global numberOfClient
            clientList[:] = [c for c in clientList if c['address'] != clientAddress]
            numberOfClient = len(clientList)

def addClient(clientName, clientAddress):
    global clientList
    clientIP, clientPort = clientAddress
    with clientCountLock: 
        clientList.append( {'address': clientAddress,
                            'port': clientPort,
                            'IP': clientIP,
                            'name': clientName,
                            'currentSubmission': None
                            })

def listen(serverSocket, numberOfClient):
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            message = message.decode()
            t2 = Thread(target=handleRequest, args=(message, clientAddress))
            t2.start()
        except (KeyboardInterrupt, SystemExit):  # FIX: Handle specific shutdown exceptions
            print("\nServer is shutting down...")
            break
        except Exception as e: # Catch and print errors (or skip)
            #print(f"An error occurred in the listen thread: {e}")
            pass

def handleRequest(message, clientAddress):
    global numberOfClient, gameState, waitingList
    clientFound = False

    # Handle the 'exit' command first, for all cases
    if message.strip().lower() == 'exit':
        with clientCountLock:
            # Check and remove from the main clientList
            for client in clientList:
                if client['address'] == clientAddress:
                    print(f"Player {client['name']}, {client['address']} has left the game")
                    clientList.remove(client)
                    numberOfClient = len(clientList)
                    return

            # Check and remove from the waitingList
            for client in waitingList:
                if client['address'] == clientAddress:
                    print(f"Waiting player {client['name']}, {client['address']} has left the game")
                    waitingList.remove(client)
                    return
        return

    # Check for existing players first
    for client in clientList:
        if client['address'] == clientAddress:
            clientFound = True

            if gameState != 1:  # Submissions only accepted during an active round
                oneClientMsg("The submission window is currently closed. Please wait for the round to start.",
                             client['address'])
                return

            if client['currentSubmission'] is not None:
                oneClientMsg("You have already submitted for this turn. Please wait for the round to end.",
                             client['address'])
                return

            try:
                submittedNum = int(message.strip())
                if 1 <= submittedNum <= 100:
                    client['currentSubmission'] = submittedNum
                    oneClientMsg(f"Number {submittedNum} received. Waiting for other players to submit.",
                        client['address'])
                #    displayMsg(f"Player {client['name']} ({clientAddress}) submitted: {submittedNum}")
                else:
                    client['currentSubmission'] = "INVALID_RANGE"
                    oneClientMsg("Number out of range (1-100)",
                                 client['address'])
                #    displayMsg(f"Player {client['name']} ({clientAddress}) submitted out-of-range: {submittedNum}")
            except ValueError:
                client['currentSubmission'] = "INVALID_INPUT"
                oneClientMsg("Invalid input.", client['address'])
                #displayMsg(f"Player {client['name']}, ({clientAddress}) submitted invalid input: '{message}'")
            return

    # Handle new players
    if not clientFound:
        if gameState == 3: # Game over state
            oneClientMsg("\nSorry, the game has ended. The server is shutting down.", clientAddress)
            return

        if gameState == 1: # Game is in an active round
            if clientAddress not in [c['address'] for c in waitingList]:
                waitingClient = {'address': clientAddress, 'name': message}
                with clientCountLock:  # FIX: Add a lock to protect the waitingList
                    waitingList.append(waitingClient)
                oneClientMsg("\nWelcome! The game is in progress. You've been added to a waiting list and will join at the start of the next round.", clientAddress)
                displayMsg(f"\nPlayer {message} ({clientAddress}) added to waiting list.")
            else:
                oneClientMsg("\nYou are already on the waiting list. Please be patient.", clientAddress)
        else: # Initial wait or between rounds (game_state 0 or 2)
            # The addClient function now handles its own lock, so this is safe.
            addClient(message, clientAddress)
            welcomeMsg = f"\nPlayer {message}, {clientAddress} has joined the game.\nCurrent players: {len(clientList)}"
            oneClientMsg(f"\nWelcome {message}! You have joined the game.", clientAddress)
            displayMsg(welcomeMsg)
            with clientCountLock:
                numberOfClient = len(clientList)

def check():
    while len(clientList) < 2:
        time.sleep(10)
        msg = "\nThe game needs to have at least two players to start..."
        broadcastMsg(msg)
        displayMsg(msg)

#Start game
gameRunning = False

#Listen to incoming requests from clients
t1 = Thread(target=listen, args=(serverSocket, numberOfClient))
t1.start()

#Set a time for 60s after opening the server for 2 players at least to joins,
# if no players or only one joined, shut down the server, the game can't start
initialWaitStartTime = time.time()
initialWaitTimeout = 60

while numberOfClient < 2:
    currentTime = time.time()
    elapsedTime = currentTime - initialWaitStartTime
    if elapsedTime >= initialWaitTimeout:
        if numberOfClient == 0:
            displayMsg(f"\nTimeout: {initialWaitTimeout} seconds passed and no clients joined. Shutting down server.")
        elif numberOfClient == 1:
            displayMsg(f"\nTimeout: {initialWaitTimeout} seconds passed. Only 1 client joined. Shutting down server.")
        serverSocket.close()
        os._exit(0)
    time.sleep(10)
    displayMsg(
        f"\nWaiting for 2 clients at least to join. Current: {numberOfClient}. Time left: {int(initialWaitTimeout - elapsedTime)}s")

# This print statement will only execute if 2 or more clients joined before timeout
print("\nGood! Minimum 2 clients connected. Waiting a moment for more players to join...")

#Last call before the start of the game, give chance for players to join
waitToJoin = 20
broadcastMsg(f"\nThe game will officially start in {waitToJoin} seconds. Stay tuned!")
displayMsg(f"\nWaiting {waitToJoin} seconds for more players to join before starting the game...")
time.sleep(waitToJoin)
broadcastMsg("\n--- THE GAME HAS OFFICIALLY BEGUN! ---\n")
displayMsg("\n--- THE GAME HAS OFFICIALLY BEGUN! ---\n")
#displayMsg("\n--- Starting the game now! ---\n")

# --- Main Game Loop: Runs rounds continuously ---
gameRunning = True
roundCount = 0

while gameRunning:
    roundCount += 1
    displayMsg(f"\n--- Starting Round {roundCount} ---\n")
    broadcastMsg(f"\n--- Starting Round {roundCount} ---\n")
    # This check is now an if statement to avoid blocking the thread
    if numberOfClient < 2:
        if numberOfClient == 1:
            winner = clientList[0]
            oneClientMsg("\nWe have a winner! You are the only player who survived.", winner['address'])
            displayMsg(f"\nThe only player who survived is {winner['name']}, ({winner['address']})")
        else:
            displayMsg("\nNo players left. Game over.")
        gameRunning = False
        gameState = 3 # Set game state to over
        break

    # 1. Announce the start of the round and prompt for submission
    # Set state to in-round
    gameState = 1
    with clientCountLock:
        for client in clientList:
            client['currentSubmission'] = None #No submissions initially

    # 2. Take submissions to process
    broadcastMsg(f"\nPlease insert a unique number from 1-100.")
    displayMsg(f"\nWaiting for user entries for Round {roundCount} (30s submission window)...")
    time.sleep(30)

    displayMsg(f"Time's up for Round {roundCount}! Processing submissions...")
    gameState = 2 # Set state to between rounds to allow new joins

    # 3. Process Submissions and Perform Eliminations After Time Limit
    with clientCountLock:
        roundSubmissionsByNumber = {}
        eliminatedThisRoundEarly = []

        for client in clientList:
            submittedNum = client['currentSubmission']
            playerName = client['name']

            eliminated = False
            eliminationReasonMsg = ""

            # Early eliminations
            if submittedNum is None:
                eliminated = True
                eliminationReasonMsg = "did not submit a number."
            elif submittedNum == "INVALID_RANGE" or submittedNum == "INVALID_INPUT":
                eliminated = True
                eliminationReasonMsg = "submitted an invalid number (not 1-100 or not a number)."
            elif submittedNum in usedNumbers:
                eliminated = True
                eliminationReasonMsg = f"submitted '{submittedNum}', which has already been used in a previous round."

            if eliminated:
                oneClientMsg(f"\nYou are eliminated! Reason: {eliminationReasonMsg}", client['address'])
                displayMsg(f"\nPlayer {playerName} ({client['address']}) ELIMINATED. Reason: {eliminationReasonMsg}")
                eliminatedThisRoundEarly.append(client)
            else:
                if submittedNum not in roundSubmissionsByNumber:
                    roundSubmissionsByNumber[submittedNum] = []
                roundSubmissionsByNumber[submittedNum].append(client)

        thisTurnUniqueValidSubmissions = set()
        survivingClientsThisRound = []

        for submittedNumber, clientsWhoSubmitted in roundSubmissionsByNumber.items():
            # If more than one player submits the same number in the round, then they are all eliminated
            if len(clientsWhoSubmitted) > 1:
                for client in clientsWhoSubmitted:
                    oneClientMsg(
                        f"\nYou are eliminated! Reason: Your number '{submittedNumber}' was also submitted by another player this round.",
                        client['address'])
                    displayMsg(
                        f"\nPlayer {client['name']} ({client['address']}) ELIMINATED. Reason: Duplicate number '{submittedNumber}' this round.")
            else:
                # If the number was only used by ONE player
                client = clientsWhoSubmitted[0]
                thisTurnUniqueValidSubmissions.add(submittedNumber) # Add unique number to a list, to update the used number list later
                survivingClientsThisRound.append(client)
                oneClientMsg(f"\nYour number {submittedNumber} is valid and unique!", client['address'])
                displayMsg(f"\nPlayer {client['name']} ({client['address']}) SURVIVED with number: {submittedNumber}")


        currentActiveClients = [c for c in clientList if c not in eliminatedThisRoundEarly]

        # The resultant client list contains those who hasn't been eliminated early and survived the round
        clientList[:] = [c for c in currentActiveClients if c in survivingClientsThisRound]

        # 4. Update Global Game State After Processing All Submissions
        usedNumbers.update(thisTurnUniqueValidSubmissions)
        numberOfClient = len(clientList)

    # 5. End of Round Status and Simplified Game End Check
    broadcastMsg(f"\n--- End of Round {roundCount} ---\n")
    displayMsg(f"\n--- End of Round {roundCount} ---\n")
#    broadcastMsg(f"Numbers used overall: {len(usedNumbers)} ({sorted(list(usedNumbers))})") # Sort for better display
    broadcastMsg(f"\nPlayers remaining: {numberOfClient}")
    displayMsg(f"\nRound {roundCount} finished. {numberOfClient} players remaining. {len(usedNumbers)} numbers used overall.")

    # Game Termination: The game ends if any of these conditions is met

    # Only one player left
    if numberOfClient == 1:
        for client in clientList:
            winnerMsg = f"\nWe have a winner! You are the only player who survived"
            oneClientMsg(winnerMsg, client['address'])
            announceWinnerMsg = f"\nThe only player who survived is {client['name']}, ({client['address']})"
            displayMsg(announceWinnerMsg)
            gameRunning = False # leave the game loop and shut down the server
            gameState = 3


    # All 100 numbers used, or the remaining numbers aren't sufficient for the number of players left
    elif numberOfClient > (100 - len(usedNumbers)) or len(usedNumbers) == 100:
        displayMsg("\nAll remaining players are winners!\n------------Winners Board:-------------")
        for client in clientList:
            winnerMsg = f"\nThe game has ended, You have survived!"
            oneClientMsg(winnerMsg, client['address'])
            announceWinnersMsg = f"\nPlayer {client['name']}, ({client['address']})"
            displayMsg(announceWinnersMsg)
            gameRunning = False
            gameState = 3

    # No players left
    elif numberOfClient == 0:
        displayMsg("\nAll players eliminated. Game over. Server shutting down.")
        broadcastMsg("\nAll players eliminated. Game over. No players left to declare winners.")
        gameRunning = False
        gameState = 3


    if gameRunning:
        # Move players from waiting list to active list
        if waitingList:
            broadcastMsg("\n--- A new round is starting. New players are now joining. ---")
            for waitingClient in waitingList:
                addClient(waitingClient['name'], waitingClient['address'])
                oneClientMsg(f"\nWelcome {waitingClient['name']}! You have now joined the game. Please get ready.", waitingClient['address'])
                displayMsg(f"\nPlayer {waitingClient['name']} ({waitingClient['address']}) moved from waiting list to active players.")

            with clientCountLock:
                numberOfClient = len(clientList)
            waitingList.clear()  # Clear the waiting list after processing

        broadcastMsg("\nNext round will begin shortly.")
        displayMsg("\nNext round will begin shortly. Waiting 15s before next round.")
        time.sleep(15)

# Once gameRunning is False, close the socket and exit (shut the server down).
displayMsg("\nServer shutting down.\n")
serverSocket.close()
os._exit(0)