# User.py
import pika
import json
import sys

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queue for user requests
channel.queue_declare(queue='user_requests')

# Get the user name and optional action and youtuber name from the command line arguments
user = sys.argv[1]
action = sys.argv[2] if len(sys.argv) > 2 else None
youtuber = sys.argv[3] if len(sys.argv) > 3 else None

# If the user is logging in
if action is None:
    # Create a login request as JSON
    request = json.dumps({
        'user': user,
        'action': 'login'
    })

# If the user is subscribing or unsubscribing to a youtuber
else:
    # Create a subscription/unsubscription request as JSON
    request = json.dumps({
        'user': user,
        'action': action,
        'youtuber': youtuber
    })

# Publish the request to the user requests queue
channel.basic_publish(exchange='', routing_key='user_requests', body=request)

# Print a message
print(f"{user} sent a {action} request")

# Declare a callback queue for the user
callback_queue = channel.queue_declare(queue='', exclusive=True).method.queue

# Consume messages from the notifications queue with the user as the routing key
channel.basic_consume(queue='notifications', on_message_callback=lambda ch, method, properties, body: receive_notifications(ch, method, properties, body, user), auto_ack=True)

# Wait for messages
print("Waiting for notifications...")
channel.start_consuming()
