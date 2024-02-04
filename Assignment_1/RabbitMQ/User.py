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

def updateSubscription(user, action, youtuber):
    # This function sends the subscription/unsubscription request to the YouTubeServer
    # Create a subscription/unsubscription request as JSON

    if(action == None):
        action = 'login'
    elif(action == 's'):
        action = 'subscribe'
    elif(action == 'u'):
        action = 'unsubscribe'

    request = json.dumps({
        'user': user,
        'action': action,
        'youtuber': youtuber
    })

    # Publish the request to the user requests queue
    channel.basic_publish(exchange='', routing_key='user_requests', body=request)

    # Print a message
    print(f"{user} sent a {action} request")

def receiveNotifications(user):
    # This function receives any notifications already in the queue for the users subscriptions and starts receiving real-time notifications for videos uploaded while the user is logged in
    # Declare a callback queue for the user
    callback_queue = channel.queue_declare(queue='', exclusive=True).method.queue

    # Consume messages from the notifications queue with the user as the routing key
    channel.basic_consume(queue='notifications', on_message_callback=lambda ch, method, properties, body: print_notification(ch, method, properties, body, user), auto_ack=True)

    # Wait for messages
    print("Waiting for notifications...")
    channel.start_consuming()

def print_notification(ch, method, properties, body, user):
    # This function prints the notifications from the notifications queue
    # Parse the notification body as JSON
    notification = json.loads(body)

    # Get the youtuber name and video name from the notification
    youtuber = notification['youtuber']
    video = notification['video']

    # Print a message
    print(f"New Notification: {youtuber} uploaded {video}")

# If the user is logging in
if action is None:
    # Call the updateSubscription function with the login action
    updateSubscription(user, 'login', None)
    # Call the receiveNotifications function
    receiveNotifications(user)

# If the user is subscribing or unsubscribing to a youtuber
else:
    # Call the updateSubscription function with the action and youtuber
    updateSubscription(user, action, youtuber)

    receiveNotifications(user)
