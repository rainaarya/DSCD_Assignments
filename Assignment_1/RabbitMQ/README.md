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

## User.py

`__init__(self, user, action=None, youtuber=None, host='127.0.0.1')`: Initializes the user, action, youtuber, connection, channel, and queue for the class.
`updateSubscription(self)`: Sends a JSON object with the user, action, and youtuber fields to the user_requests queue and prints a success message. The action can be login, subscribe, or unsubscribe.
`receiveNotifications(self)`: Receives notifications from the user-specific queue and prints them to the console.
`print_notification(ch, method, properties, body, user)`: A static method that parses the notification body as a JSON object and extracts the youtuber and video fields. It prints the notification message to the console.
The main block of the file takes the user, action, and youtuber arguments from the command line and creates an instance of the UserClient class. It then calls the updateSubscription and receiveNotifications methods. It also handles the keyboard interrupt and closes the connection.

## Running The Application

1. Start the YoutubeService
   `python YoutubeService.py`
2. Run the Youtuber service to publish a video (in a new terminal window)
    `python Youtuber.py TomScott After ten years, it's time to stop weekly videos.`
3. Run the User service to just log in, or unsubscribe or subscribe a youtuber
      3.1 Run the User service to log in, subscribe to a YouTuber, and receive notifications
          `python User.py username s TomScott`

     3.2 Run the User service to log in, unsubscribe to a YouTuber, and receive notifications
          `python User.py username u TomScott`

     3.3 Run the User service to log in and receive notifications
          `python User.py username`

Note: Steps 2 and 3 can be done in any order but make sure that you subscribe to a youtuber that exists


Note: Replace any placeholder paths, IP addresses, or ports with actual values used in your environment. This readme assumes that the YoutubeService.py, User.py, and Youtuber.py scripts are located in the same directory and are run from the command line.
