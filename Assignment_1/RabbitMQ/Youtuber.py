# Youtuber.py
import pika
import json
import sys

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queue for youtuber requests
channel.queue_declare(queue='youtuber_requests')

# Get the youtuber name and video name from the command line arguments
youtuber = sys.argv[1]
video = sys.argv[2]

# Create a video upload request as JSON
request = json.dumps({
    'youtuber': youtuber,
    'video': video
})

# Publish the request to the youtuber requests queue
channel.basic_publish(exchange='', routing_key='youtuber_requests', body=request)

# Print a message
print(f"{youtuber} published {video}")

# Close the connection
connection.close()
