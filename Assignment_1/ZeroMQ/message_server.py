import zmq
import json

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")  # Bind server to this port.
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # Set timeout for receive operations in milliseconds.

    groups = {}  # Store group information.

    try:
        while True:
            try:
                message = socket.recv_json()
                action = message['action']

                if action == 'register':
                    group_name = message['group_name']
                    ip_port = message['ip_port']
                    print(f"JOIN REQUEST FROM {ip_port}")
                    groups[ip_port] = group_name
                    response = "SUCCESS"
                    socket.send_string(response)

                elif action == 'get_group_list':
                    user_uuid = message['user_uuid']
                    print(f"GROUP LIST REQUEST FROM {user_uuid}")
                    group_list = [f"{name} - {ip_port}" for ip_port, name in groups.items()]
                    socket.send_json(group_list)

            except zmq.Again:
                # Timeout occurred, no message received
                continue  # Go back to the start of the loop and try again

    except KeyboardInterrupt:
        print("Shutting down server...")

    finally:
        socket.close()
        context.term()
        print("Server shut down.")

if __name__ == "__main__":
    print("Starting message server on port 5555...")
    main()
