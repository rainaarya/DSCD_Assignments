import pika
import json

class YoutubeServer:
    def __init__(self, host='127.0.0.1'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='user_requests')
        self.channel.queue_declare(queue='youtuber_requests')
        self.channel.queue_declare(queue='notifications')
        self.users = {}
        self.youtubers = {}
        self.subscriptions = {}

    def consume_user_requests(self, ch, method, properties, body):
        request = json.loads(body)
        user = request['user']
        action = request['action']

        if action == 'login':
            if user not in self.users:
                self.users[user] = []
            print(f"{user} logged in")  # Added print statement for login
        elif action in ['subscribe', 'unsubscribe']:
            if user not in self.users:
                self.users[user] = []
            youtuber = request['youtuber']
            sub_action = "subscribed" if action == 'subscribe' else "unsubscribed"
            if action == 'subscribe':
                if youtuber not in self.users[user]:
                    self.users[user].append(youtuber)
                if youtuber not in self.subscriptions:
                    self.subscriptions[youtuber] = []
                if user not in self.subscriptions[youtuber]:
                    self.subscriptions[youtuber].append(user)
            else:
                if youtuber in self.users[user]:
                    self.users[user].remove(youtuber)
                if youtuber in self.subscriptions and user in self.subscriptions[youtuber]:
                    self.subscriptions[youtuber].remove(user)
            print(f"{user} {sub_action} to {youtuber}")  # Added print statement for subscribe/unsubscribe

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume_youtuber_requests(self, ch, method, properties, body):
        request = json.loads(body)
        youtuber = request['youtuber']
        video = request['video']

        if youtuber not in self.youtubers:
            self.youtubers[youtuber] = []
        self.youtubers[youtuber].append(video)

        self.notify_users(youtuber, video)
        print(f"{youtuber} uploaded {video}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def notify_users(self, youtuber, video):
        notification = json.dumps({'youtuber': youtuber, 'video': video})
        subscribers = self.subscriptions.get(youtuber, [])
        for user in subscribers:
            user_queue = f"{user}_notifications"
            self.channel.queue_declare(queue=user_queue)
            self.channel.basic_publish(exchange='', routing_key=user_queue, body=notification)

    def start_server(self):
        try:
            self.channel.basic_consume(queue='user_requests', on_message_callback=self.consume_user_requests)
            self.channel.basic_consume(queue='youtuber_requests', on_message_callback=self.consume_youtuber_requests)
            print("YouTube server is running...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down...")
            self.connection.close()

if __name__ == "__main__":
    server = YoutubeServer('0.0.0.0')
    server.start_server()
