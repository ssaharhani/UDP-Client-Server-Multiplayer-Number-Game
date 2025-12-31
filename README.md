# Project Specifications – UDP Client-Server Multiplayer Number Game

This project involves implementing a multiplayer number submission game using **UDP socket programming**. The game tests attentiveness and strategic thinking in a dynamic, round-based environment.

## Game Overview
The server manages the game flow, ensures fairness, manages client states, and enforces rules.
* **Starting Condition:** The game begins when at least two active clients are connected.
* **Joining/Leaving:** Clients can join or leave at any time.
* **Gameplay:** Each round, clients submit a unique number (1–100).
* **Elimination:** If a client submits a number already used in the current or any previous round, they are eliminated and their connection is closed.
* **Winning Conditions:**
    1.  Only one client remains.
    2.  All valid numbers (1–100) have been used while multiple clients are still connected.

---

## a. Server Responsibilities

* **Connection Management:** * Listens on **port 5012**.
    * Identifies clients by IP address and port number.
    * Maintains an active list of connected clients.
* **Game Initialization:** Broadcasts a start message once at least two clients are connected.
* **Round Management:**
    * Requests a number (1–100) from all active clients.
    * Enforces a **60-second time limit** for submissions.
    * Verifies number uniqueness against all previous rounds.
* **Client Elimination:** Notifies clients of elimination and closes their connection upon invalid submissions.
* **End-of-Game Detection:** * Checks if only one client remains.
    * Checks if no unused numbers remain.
    * Broadcasts termination messages and shuts down gracefully.
* **Broadcast Messages:** Sends updates on the number of remaining players and available numbers after each round.

---

## b. Server Terminal Output

* Confirmation of server start on port 5012.
* Connection/disconnection notifications (including IP and port).
* Round start and broadcast logs.
* Display of submitted numbers, client identifiers, and validation results.
* Elimination notifications.
* Termination announcement and list of winners.
* Server shutdown message.

---

## c. Client Responsibilities

* **Connecting to the Server:** Connects via IP and port; submits a username upon joining.
* **Game Participation:**
    * May join or leave at any time.
    * Receives prompts to submit a number (1–100) each round.
    * Must attempt to provide a unique number (history is not shared with clients).
* **Receiving Notifications:** Listens for round starts, submission status, eliminations, and game results.

---

## d. Client Terminal Output

* Confirmation of successful connection.
* Prompts for number entry at the start of each round.
* Confirmation of number submission.
* Notifications for invalid/duplicate numbers.
* Notification of elimination or victory.
* Notification of server shutdown.

---
> **NOTE:** This project was done as part of the Computer Networks course in Birzeit University, T1243.

> **Project Info** > ENCS3320 - Project
