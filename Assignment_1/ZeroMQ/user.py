import zmq
import uuid

# Generate a unique ID for the user at instance creation
user_uuid = str(uuid.uuid1())

def send_group_request(action, group_ip_port):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{group_ip_port}")  # Connect to the group server

    message = {
        'action': action,
        'user_uuid': user_uuid  
    }
    socket.send_json(message)
    response = socket.recv_json()
    print(response['response'])

def get_group_list():
    action = 'get_group_list'
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")  # Connect to the message server.

    message = {
        'action': action,
        'user_uuid': user_uuid  
    }
    socket.send_json(message)
    group_list = socket.recv_json()
    for group in group_list:
        print(group)

def get_messages(group_ip_port, timestamp=None):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{group_ip_port}")
    action = 'getMessage'
    message = {
        'action': action,
        'user_uuid': user_uuid,
        'timestamp': timestamp
    }
    socket.send_json(message)
    response = socket.recv_json()
    if response['response'] == 'SUCCESS':
        messages = response['messages']
        for msg in messages:
            print(f"{msg['user_uuid']} : {msg['message']} ({msg['timestamp']})")
    else:
        print("User is not a member of this group. Please join the group first.")

def send_message(group_ip_port, message_text):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{group_ip_port}")
    action = 'sendMessage'
    message = {
        'action': action,
        'user_uuid': user_uuid,
        'message': message_text
    }
    socket.send_json(message)
    response = socket.recv_json()
    print(response['response'])

def read_large_text_from_terminal():
    print("\nEnter your text (type 'END' on a new line to finish):\n")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    text = "\n".join(lines)
    return text


if __name__ == "__main__":
    commands = {
        "join_group": ("Join a group", "IP:PORT"),
        "leave_group": ("Leave a group", "IP:PORT"),
        "get_group_list": ("Get list of groups", "no parameters"),
        "get_messages": ("Get messages from a group", "IP:PORT, optional timestamp (HH:MM:SS) )"),
        "send_message": ("Send a message to a group", "IP:PORT"),
        "exit": ("Exit the program", "no parameters")
    }

    while True:
        print("\nAvailable Commands:")
        for cmd, (desc, params) in commands.items():
            print(f"{cmd}: {desc} - Parameters: {params}")

        user_input = input("Enter command and parameters(if any) separated by space : ").split(' ')

        command = user_input[0]
        group_ip_port = user_input[1] if len(user_input) > 1 else None
        timestamp = user_input[2] if len(user_input) > 2 else None
        
        if command == "exit":
            break
        
        elif command == "join_group" and group_ip_port:
            send_group_request("joinGroup", group_ip_port)
            
        elif command == "leave_group" and group_ip_port:
            send_group_request("leaveGroup", group_ip_port)
            
        elif command == "get_group_list":
            get_group_list()
            
        elif command == "get_messages" and group_ip_port:
            get_messages(group_ip_port, timestamp)
            
        elif command == "send_message" and group_ip_port:
            large_text = read_large_text_from_terminal()
            send_message(group_ip_port, large_text)
            
        else:
            print("Invalid command")
