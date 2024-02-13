# Youtuber.py
import pika
import json
import sys

class YoutuberClient:
    def __init__(self, youtuber, video, host='127.0.0.1'):
        self.youtuber = youtuber
        self.video = video
        credentials = pika.PlainCredentials('user', 'user')
        parameters = pika.ConnectionParameters(host, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='youtuber_requests')

    def publishVideo(self):
        request = json.dumps({
            'youtuber': self.youtuber,
            'video': self.video
        })

        self.channel.basic_publish(exchange='', routing_key='youtuber_requests', body=request)
        print(f"SUCCESS: {self.youtuber} published {self.video}")

    def closeConnection(self):
        self.connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python Youtuber.py <youtuber> <video>")
        sys.exit(1)

    youtuber = sys.argv[1]
    video = ' '.join(sys.argv[2:])

    client = YoutuberClient(youtuber, video, '10.190.0.2')
    client.publishVideo()
    client.closeConnection()