# User.py
import pika
import json
import sys
from functools import partial

class UserClient:
    def __init__(self, user, action=None, youtuber=None, host='127.0.0.1'):
        self.user = user
        self.action = action
        self.youtuber = youtuber
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='user_requests')

    def updateSubscription(self):
        if self.action is None:
            self.action = 'login'
        elif self.action == 's':
            self.action = 'subscribe'
        elif self.action == 'u':
            self.action = 'unsubscribe'

        request = json.dumps({
            'user': self.user,
            'action': self.action,
            'youtuber': self.youtuber
        })

        self.channel.basic_publish(exchange='', routing_key='user_requests', body=request)
        print(f"SUCCESS: {self.user} sent a {self.action} request")

    def receiveNotifications(self):
        user_queue = f"{self.user}_notifications"
        self.channel.queue_declare(queue=user_queue)

        on_message_callback_with_user = partial(self.print_notification, user=self.user)
        self.channel.basic_consume(queue=user_queue, on_message_callback=on_message_callback_with_user, auto_ack=True)

        print("Waiting for notifications...")
        self.channel.start_consuming()

    @staticmethod
    def print_notification(ch, method, properties, body, user):
        notification = json.loads(body)
        youtuber = notification['youtuber']
        video = notification['video']
        print(f"New Notification: {youtuber} uploaded {video}")

if __name__ == "__main__":
    try:
        user = sys.argv[1]
        action = sys.argv[2] if len(sys.argv) > 2 else None
        youtuber = sys.argv[3] if len(sys.argv) > 3 else None

        client = UserClient(user, action, youtuber, '127.0.0.1')
        client.updateSubscription()
        client.receiveNotifications()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Closing connection...")
        client.connection.close()
        sys.exit(0)