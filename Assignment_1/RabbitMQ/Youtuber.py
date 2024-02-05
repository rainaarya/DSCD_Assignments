# Youtuber.py
import pika
import json
import sys

class YoutuberClient:
    def __init__(self, youtuber, video, host='127.0.0.1'):
        self.youtuber = youtuber
        self.video = video
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
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
    youtuber = sys.argv[1]
    video = ' '.join(sys.argv[2:])

    client = YoutuberClient(youtuber, video, '127.0.0.1')
    client.publishVideo()
    client.closeConnection()