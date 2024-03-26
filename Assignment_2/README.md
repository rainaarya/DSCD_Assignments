# Raft Consensus Algorithm with Leader Lease Modification

## Introduction
This project implements a modified version of the Raft consensus algorithm, similar to those used by geo-distributed database clusters such as CockroachDB or YugabyteDB. Raft is a distributed consensus algorithm that ensures fault tolerance and consistency in a cluster of nodes. The algorithm operates through leader election, log replication, and commitment of entries across the cluster.

The goal is to build a distributed key-value store that maps string keys to string values. The Raft cluster maintains this database and ensures fault tolerance and strong consistency. Clients can request the server to perform operations on the database reliably.

## Raft Modification (for faster reads)
In the traditional Raft algorithm, the leader needs to exchange heartbeats with a majority of peers before responding to a read request. This introduces a network hop between peers for each read operation, resulting in high read latencies, especially in multi-region geo-distributed databases where nodes are located far apart.

To address this issue, the concept of leader lease is introduced. The leader acquires a time-based lease that is propagated through the heartbeat mechanism. With well-behaved clocks, linearizable reads can be obtained without the round-trip latency penalty.

## Leader Lease
A leader lease is a token that is valid for a certain period, known as the lease duration. Only the leader node can acquire a lease, and at any given time, only one lease can exist in the cluster.

The leader acquires and renews the lease using the heartbeat mechanism. When the leader acquires or renews the lease, it starts a countdown timer equal to the lease duration. If the leader fails to renew the lease within this duration, it must step down from being the leader.

The leader also propagates the end time of the acquired lease in its heartbeat messages. Follower nodes keep track of this leader lease timeout and use this information in the next election process.

## Leader Election
During a leader election, a voter must propagate the old leader's lease timeout known to that voter to the new candidate it is voting for. Upon receiving a majority of votes, the new leader must wait out the longest old leader's lease duration before acquiring its own lease. The old leader steps down and no longer functions as a leader upon the expiry of its leader lease.

## Implementation Details

### Overview
Each node in the Raft cluster is implemented as a separate process hosted on a separate Virtual Machine (VM) on Google Cloud. The client can reside either in a Google Cloud VM or on a local machine. The nodes communicate with each other and with the client using gRPC.

### Pseudo Code
The implementation follows the pseudo code provided in the assignment description. It handles various edge cases and scenarios that occur during the Raft algorithm execution.

### Storage and Database Operations
The nodes store key-value pairs, where both the key and value are strings. The data is persisted on disk, even after a node is stopped and restarted. The data is stored in a human-readable format (.txt files) along with other important metadata such as `commitLength`, `Term`, and `NodeID`.

The supported database operations are:
- `SET <key> <value>`: Maps the specified key to the specified value.
- `GET <key>`: Returns the latest committed value of the specified key. If the key doesn't exist, an empty string is returned.

Additionally, nodes can initiate an empty instruction called the `NO-OP` operation, which is used for maintaining the heartbeat and leader lease.

### Client Interaction
The client stores the IP addresses and ports of all the nodes in the cluster, along with the current leader ID. It sends `GET` and `SET` requests to the leader node. In case of a failure, the client updates its leader ID and resends the request to the updated leader. The client continues sending the request until it receives a success reply from any node.

### Standard Raft RPCs
The implementation uses two RPCs for communication between nodes: `AppendEntry` and `RequestVote`. These RPCs are explained in detail in the original Raft paper.

### Election Functionalities
Nodes implement the following functionalities related to the leader election process:
- Start Election: Follower nodes keep an election timer and listen for heartbeat events or vote requests. If no event is received within the election timeout duration, the node becomes a candidate, increments the term number, and sends vote requests to other nodes.
- Receive Voting Request: A node votes for a candidate only when certain conditions are met, as described in the pseudo code.
- Leader State: If a candidate node receives a majority of votes, it becomes the leader. The new leader waits for the maximum of the old leader's lease timer and its own before acquiring its own lease. Once the old lease timer has run out, the node starts its lease timer, appends a `NO-OP` entry to the log, and sends heartbeats to all other nodes.

### Log Replication Functionalities
The nodes perform the following functionalities to replicate logs correctly and maintain log integrity:
- Periodic Heartbeats: The leader sends periodic heartbeats to all nodes to maintain its leader state. The leader also reacquires its lease at each heartbeat by restarting the lease timer and propagating the lease duration.
- Replicate Log Request: When the leader receives a client `SET` request, it uses the `AppendEntriesRPC` to replicate the log entry to all nodes. For `GET` requests, the leader can immediately return the value if it has acquired the lease.
- Replicate Log Reply: A node accepts an `AppendEntriesRPC` request only when certain conditions are met, as described in the pseudo code.

### Committing Entries
The leader commits an entry only when a majority of nodes have acknowledged appending the entry, and the latest entry to be committed belongs to the same term as that of the leader. Follower nodes use the `LeaderCommit` field in the `AppendEntry` RPC to commit entries.

### Print Statements & Dump File
The implementation includes print statements to provide information about the state of each node and the operations being performed. Each node generates a dump file that contains these print statements, along with timestamps.

## Code Explanation

### raft.py
The `raft.py` file contains the implementation of the Raft node. It defines the `RaftNode` class, which inherits from the `RaftServicer` class generated by gRPC.

The `RaftNode` class maintains the state of the node, including the current term, voted-for node, log entries, commit length, current leader, and other relevant information. It also manages timers for election, heartbeat, and leader lease.

The class provides the following key methods:
- `load_state`: Loads the node's state from disk when the node starts up.
- `save_state`: Saves the node's state to disk.
- `start_election_timer`, `start_heartbeat_timer`, `start_lease_timer`: Start the respective timers.
- `cancel_election_timer`, `cancel_heartbeat_timer`, `cancel_lease_timer`: Cancel the respective timers.
- `start_election`: Initiates the election process when the election timer times out.
- `become_leader`: Transitions the node to the leader state when it receives a majority of votes.
- `step_down`: Transitions the node to the follower state.
- `append_no_op_entry`: Appends a `NO-OP` entry to the log.
- `send_heartbeats`: Sends heartbeat messages to all follower nodes.
- `replicate_log_async`: Replicates log entries to a follower node asynchronously.
- `commit_log_entries`: Commits log entries that have been acknowledged by a majority of nodes.
- `RequestVote`, `AppendEntries`, `ServeClient`: RPC methods for handling RequestVote, AppendEntries, and client requests, respectively.

The `main` function in `raft.py` sets up the Raft node and starts the gRPC server.

### client.py
The `client.py` file contains the implementation of the Raft client. It provides a command-line interface for interacting with the Raft cluster.

The client performs the following steps:
1. Discovers the current leader by sending a `GET __leader__` request to each node until it receives a success response.
2. Prompts the user to enter a command (`GET <key>` or `SET <key> <value>`).
3. Sends the command to the leader node and waits for a response.
4. If the leader changes, the client updates its leader information and resends the request to the new leader.
5. Prints the response received from the leader.

The client continues to interact with the cluster until it is interrupted by the user (`Ctrl+C`).

## How to Run the Code

### Prerequisites
- Python 3.x installed on all machines (VMs and client machine)
- gRPC and Protocol Buffers installed on all machines
- Google Cloud SDK installed and configured on the client machine

### Setup
1. Clone the project repository on all machines.
2. Install the required dependencies by running the following command in the project directory:

   ```
   pip install grpcio grpcio-tools
   ```
3. Generate the gRPC code by running the following command in the project directory:

   ```
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto
   ```

### Running the Raft Cluster
1. On each VM, navigate to the project directory and run the following command:
   ```
   python raft.py <node_id> <num_nodes>
   ```
   Replace `<node_id>` with the unique identifier of the node (e.g., 0, 1, 2, etc.) and `<num_nodes>` with the total number of nodes in the cluster.
   
   For example, to start a node with ID 0 in a 5-node cluster, run:
   ```
   python raft.py 0 5
   ```

2. Repeat step 1 for each node in the cluster.

### Running the Client
1. On the client machine, navigate to the project directory and run the following command:
   ```
   python client.py
   ```

2. When prompted, enter the number of nodes in the cluster.

3. The client will attempt to connect to the leader node. If a leader is found, it will display the leader's ID.

4. Enter commands in the format `GET <key>` or `SET <key> <value>` to interact with the key-value store.

5. The client will send the commands to the leader and display the response received.

6. To exit the client, press `Ctrl+C`.