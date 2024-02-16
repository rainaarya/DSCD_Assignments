# 📨 Messaging System

This messaging system is designed to facilitate communication within groups. It utilizes ZeroMQ for messaging patterns, providing a simple and efficient way to implement messaging functionalities including group registration, message sending, and retrieval. The system is composed of three primary scripts:

1. `message_server.py`: Manages group registrations and provides a list of groups.
2. `group.py`: Handles group-specific actions such as joining, leaving, and message management within a group.
3. `user.py`: Allows users to interact with groups, send messages, and retrieve messages.

## 📦 Installation:

Before running the system, ensure you have Python and ZeroMQ installed on your system. You can install ZeroMQ by following the instructions on the official ZeroMQ website. Python dependencies can be installed via pip:

```
pip install pyzmq
pip install uuid
pip install json
pip install datetime
```

## 🏃‍♂️ Running the System

### 🚀 Starting the Message Server

To start the message server, which manages group registrations and lists, run:

```
python message_server.py
```

This will start the server on port 5555, listening for group registration requests and providing a list of available groups to users.

### 🎉 Creating a Group

To create a group, you need to specify a group name and the IP address with port where the group server will listen for incoming connections. Run:

```
python group.py <group_name> <ip_port_of_group> <main_server_address>
```

For example: `python group.py "Cool Group" 192.168.3.97:5560 192.168.1.10`
This will be used to register the group to the main server and start listening for user requests on the specified IP and port.

### 📝 User Commands

Users can interact with the system through the `user.py` script. Available commands are:

- `join_group IP:PORT`: Join a specified group. 🤝
- `leave_group IP:PORT`: Leave a specified group.👋
- `get_group_list`: Retrieve a list of available groups.📜
- `get_messages IP:PORT <optional timestamp>`: Retrieve messages from a group, optionally starting from a specific timestamp.📥
- `send_message IP:PORT`: Send a message to a group. You'll be prompted to enter the message text, ending with END on a new line.📤
- `exit`: Exit the program.🚪

To run a command, execute:

```
python user.py <main_server_address>
```

Then, enter the desired command and follow the prompts.

## 🏗️ System Architecture:

- **Message Server (`message_server.py`):** Utilizes a ZeroMQ REP socket to manage group registrations and queries for group lists. It binds to a predefined port and listens for JSON-formatted messages.

- **Group Server (`group.py`):** Manages group-specific functionalities using a ZeroMQ ROUTER socket for handling user requests such as joining/leaving groups and sending/receiving messages. It connects to the message server for registration and binds to a specified port for user communications.

- **User Client (`user.py`):** Interacts with both the message server and group servers through ZeroMQ REQ sockets. It allows users to perform actions like joining groups, sending messages, and fetching messages.

## 📚 Code Explanation in Each File

- **`message_server.py`:**
  - 🧩 Initializes a ZeroMQ context and creates a REP socket. 
  - 📋 Manages group registrations and responses to queries for group lists.
- **`group.py`:**
  - 🧵 Uses ZeroMQ for network communication and threading to handle user requests concurrently. 
  - 📨 Handles group-specific actions such as joining, leaving, sending, and retrieving messages. 

- **`user.py`:**
  - 🆔 Generates a unique UUID for user identification. 
  - 🎛️ Implements functions for user interaction with group and message servers. 

---