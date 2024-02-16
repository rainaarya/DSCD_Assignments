# Implementing a YouTube-like application using RabbitMQ


A simplified version of a YouTube application using RabbitMQ. The system consists of three components: User, YoutubeServer and Youtuber

### YouTuber

Youtuber is a service that allows YouTubers to publish videos on the YouTube server.
Youtubers can publish videos by sending simple messages to the YouTube server, including the video name and the YouTuber’s name.

### User
Users can subscribe or unsubscribe to YouTubers by sending messages to the YouTube server.
Users will receive real-time notifications whenever a YouTuber they subscribe to uploads a new video.
Note that YouTubers and users cannot directly communicate with each other; only through the YouTube server can they do so.
Users can log in by running the User.py script with their name as the first argument. Optionally, they can subscribe or unsubscribe to a YouTuber using the second and third arguments. (See deliverables).
Whenever a user logs in, it immediately receives all the notifications of videos uploaded by its subscriptions while the user was logged out.

### YouTubeServer
The YouTube server consumes messages from Users and YouTubers and stores them as data, maintaining a list of YouTubers and their videos, and all users and their subscriptions.
It also processes subscription and unsubscription requests from users.
The server sends notifications to all subscribers of a YouTuber whenever they upload a new video.

## Dependencies

Python 3.x
Erlang 25.x - 2.6.2x
RabbitMQ 3.12.10 - 3.12.12

## Installation

Before running the application, ensure you have Python and pip installed. Then, install the required Python packages:

`pip install pika`

## Files Description

`YoutubeServer.py` This file sets up and runs the YouTube server. 
`Youtuber.py` This file represents the Youtuber service. 
`User.py` This file represents the User service.

## YoutubeServer.py Overview

`__init__(self, host='127.0.0.1')`: Initializes the connection, channel, queues, and dictionaries for the class.
`consume_user_requests(self, ch, method, properties, body)`: Processes user requests for login, subscribe, or unsubscribe actions.
`consume_youtuber_requests(self, ch, method, properties, body)`: Processes youtuber requests for uploading videos and notifies the subscribers.
`notify_users(self, youtuber, video)`: Sends notifications to the users who have subscribed to the given youtuber.
`start_server(self)`: Starts the server by consuming messages from the queues and handles the keyboard interrupt.

## Youtuber.py

`__init__(self, youtuber, video, host='127.0.0.1')`: Initializes the youtuber, video, connection, channel, and queue for the class.
`publishVideo(self)`: Publishes a JSON object with the youtuber and video fields to the youtuber_requests queue and prints a success message.
`closeConnection(self)`: Closes the connection to the message broker.
The main block of the file takes the youtuber and video arguments from the command line and creates an instance of the YoutuberClient class. It then calls the publishVideo and closeConnection methods.
