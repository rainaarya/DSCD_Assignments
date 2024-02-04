# YoutubeServer.py
import pika
import json

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queues for user requests, youtuber requests, and notifications
channel.queue_declare(queue='user_requests')
channel.queue_declare(queue='youtuber_requests')
channel.queue_declare(queue='notifications')

# Create dictionaries to store users, youtubers, and subscriptions
users = {}
youtubers = {}
subscriptions = {}

def consume_user_requests(ch, method, properties, body):
    # This function consumes login and subscription/unsubscription requests from users
    # Parse the request body as JSON
    request = json.loads(body)

    # Get the user name and action from the request
    user = request['user']
    action = request['action']

    print(f"{user} logged in")

    # If the user is logging in
    if action == 'login':

        print("In login")
        # Add the user to the users dictionary if not already present
        if user not in users:
            users[user] = []
        # Print a message
        #print(f"{user} logged in")
        # Send any pending notifications to the user
        send_notifications(user)
    
    # If the user is subscribing or unsubscribing to a youtuber
    elif action in ['subscribe', 'unsubscribe']:

        print("in subscribe/unsubscribe")
        
        if user not in users:
            users[user] = []
        
        # Get the youtuber name from the request
        youtuber = request['youtuber']
        # If the user is subscribing
        if action == 'subscribe':
            # Add the youtuber to the user's subscriptions list if not already present
            if youtuber not in users[user]:
                users[user].append(youtuber)
            # Add the user to the youtuber's subscribers list if not already present
            if youtuber not in subscriptions:
                subscriptions[youtuber] = []
            if user not in subscriptions[youtuber]:
                subscriptions[youtuber].append(user)
        # If the user is unsubscribing
        else:
            # Remove the youtuber from the user's subscriptions list if present
            if youtuber in users[user]:
                users[user].remove(youtuber)
            # Remove the user from the youtuber's subscribers list if present
            if youtuber in subscriptions and user in subscriptions[youtuber]:
                subscriptions[youtuber].remove(user)
        # Print a message
        print(f"{user} {action}d to {youtuber}")
    
    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_youtuber_requests(ch, method, properties, body):
    # This function consumes video upload requests from youtubers
    # Parse the request body as JSON
    request = json.loads(body)

    # Get the youtuber name and video name from the request
    youtuber = request['youtuber']
    video = request['video']

    # Add the youtuber to the youtubers dictionary if not already present
    if youtuber not in youtubers:
        youtubers[youtuber] = []
    # Add the video to the youtuber's videos list
    youtubers[youtuber].append(video)

    # Print a message
    print(f"{youtuber} uploaded {video}")

    # Notify the subscribers of the youtuber
    notify_users(youtuber, video)

    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

def notify_users(youtuber, video):
    # This function sends notifications to all users who subscribe to the youtuber
    # Create a notification message as JSON
    notification = json.dumps({
        'youtuber': youtuber,
        'video': video
    })

    # Get the subscribers of the youtuber
    subscribers = subscriptions.get(youtuber, [])

    print(f"Subscribers of {youtuber}: {subscribers}")
    # For each subscriber
    for user in subscribers:
        # Publish the notification to the notifications queue with the user as the routing key
        channel.basic_publish(exchange='', routing_key='notifications', body=notification, properties=pika.BasicProperties(
            reply_to=user
        ))

def send_notifications(user):
    # This function sends any pending notifications to the user
    # Declare a callback queue for the user
    callback_queue = channel.queue_declare(queue='', exclusive=True).method.queue

    # Consume messages from the notifications queue with the user as the routing key
    channel.basic_consume(queue='notifications', on_message_callback=lambda ch, method, properties, body: receive_notifications(ch, method, properties, body, user), auto_ack=True)

    # Wait for messages for a short time
    connection.process_data_events(time_limit=1)

    # Cancel the consumption
    channel.basic_cancel(callback_queue)

def receive_notifications(ch, method, properties, body, user):
    # This function receives notifications from the notifications queue and prints them
    # Parse the notification body as JSON
    notification = json.loads(body)

    # Get the youtuber name and video name from the notification
    youtuber = notification['youtuber']
    video = notification['video']

    # Print a message
    print(f"New Notification: {youtuber} uploaded {video}")

# Start consuming user requests and youtuber requests
channel.basic_consume(queue='user_requests', on_message_callback=consume_user_requests)
channel.basic_consume(queue='youtuber_requests', on_message_callback=consume_youtuber_requests)

# Start the server
print("YouTube server is running...")
channel.start_consuming()
