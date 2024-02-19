Messaging System

This messaging system is designed to facilitate communication within groups. It utilizes ZeroMQ for messaging patterns, providing a simple and efficient way to implement messaging functionalities including group registration, message sending, and retrieval. The system is composed of three primary scripts:
1)  message_server.py: Manages group registrations and provides a list of groups.
2)  group.py: Handles group-specific actions such as joining, leaving, and message management within a group.
3)  user.py: Allows users to interact with groups, send messages, and retrieve messages.

Installation:

Before running the system, ensure you have Python and ZeroMQ installed on your system. You can install ZeroMQ by following the instructions on the official ZeroMQ website. Python dependencies can be installed via pip:

pip install pyzmq
pip install uuid
pip install json
pip install datetime

Running the System:

Starting the Message Server
To start the message server, which manages group registrations and lists, run:

python message_server.py

This will start the server on port 5555, listening for group registration requests and providing a list of available groups to users.

Creating a Group:
To create a group, you need to specify a group name and the IP address with port where the group server will listen for incoming connections. Run:

python group.py <group_name> <ip_port>

For example: python group.py "Cool Group" 192.168.3.97:5560
This will register the group with the message server and start listening for user requests on the specified IP and port.

User Commands:
Users can interact with the system through the user.py script. Available commands are:

join_group IP:PORT: Join a specified group.
leave_group IP:PORT: Leave a specified group.
get_group_list: Retrieve a list of available groups.
get_messages IP:PORT, optional timestamp (HH:MM:SS): Retrieve messages from a group, optionally starting from a specific timestamp.
send_message IP:PORT: Send a message to a group. You'll be prompted to enter the message text, ending with END on a new line.
exit: Exit the program.
To run a command, execute:

python user.py

Then, enter the desired command and follow the prompts.

System Architecture:

Message Server (message_server.py): Utilizes a ZeroMQ REP socket to manage group registrations and queries for group lists. It binds to a predefined port and listens for JSON-formatted messages.

Group Server (group.py): Manages group-specific functionalities using a ZeroMQ ROUTER socket for handling user requests such as joining/leaving groups and sending/receiving messages. It connects to the message server for registration and binds to a specified port for user communications.

User Client (user.py): Interacts with both the message server and group servers through ZeroMQ REQ sockets. It allows users to perform actions like joining groups, sending messages, and fetching messages.

Code Explanation in Each File:

message_server.py:

1)  This script acts as the central server for the messaging system. It uses ZeroMQ to listen for requests from group servers wanting to register themselves and from users requesting a list of available groups. Here's what it does:

2)  ZeroMQ Context and Socket Setup: Initializes a ZeroMQ context and creates a REP (reply) socket to handle incoming connections on port 5555. It sets a receive timeout to handle situations where no request is received within a specified period.

3)  Group Management: Maintains a dictionary named groups where group information is stored, indexed by ip_port with the group name as the value. This allows for quick lookups and management of groups.

4)  Request Handling: The server enters an infinite loop, listening for JSON-formatted requests. Based on the action field in the request, it performs different operations:

5)  Register: When a group server wants to register, it sends a register action with its group_name and ip_port. The server then adds this information to the groups dictionary and responds with "SUCCESS".

6)  Get Group List: When a request with the get_group_list action is received (typically from a user), the server compiles a list of available groups from the groups dictionary and sends it back as a JSON list.

7)  Timeout Handling: Implements exception handling for timeouts (using zmq.Again) to ensure the server doesn't halt if a request isn't received within the expected timeframe.

8)  Cleanup: On a keyboard interrupt (Ctrl+C), it gracefully shuts down the server by closing the socket and terminating the ZeroMQ context.

group.py:

1)  This script manages group-specific actions and communications. It allows groups to register with the central message server and handles user requests to join/leave the group, send messages, and retrieve messages. Here's an overview:

2)  ZeroMQ and Threading: Uses ZeroMQ for network communication and Python's threading to handle user requests concurrently.

3)  Group Registration: The register_group function sends a registration request to the message_server.py for the group with its name and listening port. Upon successful registration, it starts a thread to handle incoming user requests.

4)  Handling User Requests: The handle_user_requests function listens for user actions such as joining the group, leaving the group, sending messages, and fetching messages. It uses a ROUTER socket to manage multiple user connections uniquely.

5)  Join/Leave Group: Adds or removes a user's UUID to a set tracking current group members.

6)  Send/Get Messages: Manages a list of messages, allowing users to send messages to the group and retrieve them. Messages can be filtered by a timestamp for fetching new messages since a specific time.

7)  Thread Management: Uses global flags and locks to safely access shared resources across threads (e.g., user set and messages list) and to signal when the server should shut down.

user.py:

1)  This script enables user interaction with the system. It allows users to perform various actions like joining groups, sending and receiving messages, and querying the list of available groups. Here's a breakdown:

2)  User Identity: Generates a unique UUID for each user instance to uniquely identify users across the system.

3)  Communication with Group and Message Server: Implements functions to send requests to the group servers (for joining/leaving groups, sending/receiving messages) and the message server (for retrieving the list of available groups).

4)  Sending and Receiving Messages: Users can send messages to groups they've joined and retrieve messages from those groups. The retrieval can be filtered based on a timestamp to get only new messages.

5)  Interactive Command Interface: Provides a simple command-line interface for users to interact with the system, allowing them to execute supported actions by entering commands.

6)  Text Input for Messages: Includes a function for reading multi-line text from the terminal, enabling users to enter longer messages conveniently.