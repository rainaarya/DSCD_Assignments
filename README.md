# 🌐 DSCD Assignments, W24 📚

This repository contains assignments related to the **Distributed Systems course at IIIT-Delhi, Winter 2024** 🎓. Each assignment focuses on different aspects and technologies used in building distributed systems.

## 🛍️ Assignment 1: Distributed Messaging Frameworks

The first assignment focuses on usage of distributed messaging frameworks (gRPC, ZeroMQ, RabbitMQ). It consists of 3 parts:

1. 🏪 [Online Shopping Platform](Assignment_1/gRPC): Uses gRPC for communication between a central marketplace, sellers, and buyers. It demonstrates the practical application of gRPC in a distributed system.

2. 💬 [WhatsApp Messaging System](Assignment_1/ZeroMQ): Utilizes ZeroMQ for messaging patterns, providing a simple and efficient way to implement messaging functionalities including group registration, message sending, and retrieval.

3. 📹 [YouTube Application](Assignment_1/RabbitMQ): Implements a YouTube-like application using RabbitMQ. It allows YouTubers to publish videos and users to subscribe to their favorite YouTubers, facilitating communication through the YouTube server.

## 🤝 Assignment 2: Modified Raft Consensus Algorithm 

The [second assignment](Assignment_2/) focuses on implementing a modified version of the Raft consensus algorithm, similar to those used by geo-distributed database clusters such as CockroachDB or YugabyteDB. It aims to build a distributed key-value store that ensures fault tolerance and strong consistency.

The concept of [leader lease](https://www.yugabyte.com/blog/low-latency-reads-in-geo-distributed-sql-with-raft-leader-leases/) is used to address the issue of high read latencies in the traditional Raft algorithm.

---

Please refer to the individual assignment directories and their respective README files for more detailed information on each assignment. 📝
