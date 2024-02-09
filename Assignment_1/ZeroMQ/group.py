import zmq
import threading
import sys
import json
import datetime
from threading import Lock



# Global flag to control thread execution
running = True
USERTELE = set()
MESSAGES = []
user_lock = Lock()  # Lock for accessing or modifying USERTELE
message_lock = Lock()  # Lock for accessing or modifying MESSAGES

def handle_user_requests(socket):
    global running, USERTELE, MESSAGES
    try:
        while running:
            if socket.poll(1000):  # Check for a message with a timeout
                message_parts = socket.recv_multipart()
                # print(f"Received message parts: {message_parts}")  # Debugging print

                if len(message_parts) < 3:
                    print("Warning: Received message with insufficient parts.")
                    continue

                # Assuming the message format is [identity, empty, content]
                sender_identity, _, message_content = message_parts[0], message_parts[1], message_parts[2]

                if not message_content:
                    print("Warning: Received empty message content.")
                    continue

                message = json.loads(message_content.decode('utf-8'))
                user_uuid = message['user_uuid']
                action = message['action']

                if action == 'joinGroup':
                    with user_lock:
                        USERTELE.add(user_uuid)
                    print(f"JOIN REQUEST FROM {user_uuid}")                  # Add user to group's user list and send a response
                    response = json.dumps({'response': 'SUCCESS'}).encode('utf-8')
                    socket.send_multipart([sender_identity, b'', response])

                elif action == 'leaveGroup':
                    with user_lock:
                        USERTELE.remove(user_uuid)
                    print(f"LEAVE REQUEST FROM {user_uuid} ")                 # Remove user from group's user list and send a response
                    response = json.dumps({'response': 'SUCCESS'}).encode('utf-8')
                    socket.send_multipart([sender_identity, b'', response])
                    
                elif action == 'sendMessage':
                    with user_lock:
                        if user_uuid in USERTELE:
                            message_text = message['message']
                            timestamp = datetime.datetime.now()
                            with message_lock:
                                MESSAGES.append({'user_uuid': user_uuid, 'message': message_text, 'timestamp': timestamp.isoformat()})
                            response = json.dumps({'response': 'SUCCESS'}).encode('utf-8')
                        else:
                            response = json.dumps({'response': 'FAILED'}).encode('utf-8')
                    print(f"MESSAGE SEND FROM {user_uuid}")
                    socket.send_multipart([sender_identity, b'', response])
                
                elif action == 'getMessage':
                    with user_lock:
                        if user_uuid in USERTELE:
                            timestamp = message.get('timestamp')
                            relevant_messages = []
                            if timestamp:
                                requested_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                                with message_lock:
                                    for msg in MESSAGES:
                                        msg_datetime = datetime.datetime.fromisoformat(msg['timestamp'])
                                        if msg_datetime >= requested_datetime:
                                            relevant_messages.append(msg)
                            else:
                                with message_lock:
                                    relevant_messages = MESSAGES.copy()
                            
                            response = json.dumps({'response': 'SUCCESS', 'messages': relevant_messages}).encode('utf-8')
                        else:
                            response = json.dumps({'response': 'FAILED'}).encode('utf-8')
                    print(f"MESSAGE REQUEST FROM {user_uuid}")
                    socket.send_multipart([sender_identity, b'', response])
                    
    except zmq.ZMQError as e:
        if running:
            print(f"Error handling user request: {e}")
    finally:
        socket.close()


def register_group(group_name, ip_port):
    global running, USERTELE
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    message = {
        'action': 'register',
        'group_name': group_name,
        'ip_port': ip_port
    }
    socket.send_json(message)
    response = socket.recv_string()
    print(response)

    socket.close()  # Close this socket as it's no longer needed

    if response == "SUCCESS":
        user_socket = context.socket(zmq.ROUTER)
        user_socket.bind(f"tcp://{ip_port}")
        thread = threading.Thread(target=handle_user_requests, args=(user_socket,))
        thread.start()
        return context, user_socket, thread  # Return these so they can be managed outside

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python group.py <group_name> <ip_port>")
        sys.exit(1)
    group_name = sys.argv[1]
    ip_port = sys.argv[2]  # Group's own IP and Port
    context, user_socket, thread = register_group(group_name, ip_port)

    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Shutting down group...")
        running = False  # Signal threads to exit
        thread.join()  # Wait for the thread to finish
        user_socket.close()
        context.term()  # Cleanly terminate the ZeroMQ context
