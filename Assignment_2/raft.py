import grpc
import raft_pb2
import raft_pb2_grpc
import random
import time
import threading
import os
import sys
from concurrent import futures
import datetime
import signal

# Constants
HEARTBEAT_INTERVAL = 1.0  # Heartbeat interval in seconds
ELECTION_TIMEOUT_MIN = 5.0  # Minimum election timeout in seconds
ELECTION_TIMEOUT_MAX = 10.0  # Maximum election timeout in seconds
LEASE_DURATION = 10  # Leader lease duration in seconds

# Raft node states
FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

class RaftNode(raft_pb2_grpc.RaftServicer):
    def __init__(self, node_id, node_addresses):
        self.node_id = node_id
        self.node_addresses = node_addresses
        self.state = FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_length = 0
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}
        self.election_timer = None
        self.heartbeat_timer = None
        self.lease_timer = None
        self.old_leader_lease_timeout = 0
        self.heartbeat_success_count = set()
        self.lease_start_time = 0
        self.data_store = {}
        self.timer_lock = threading.Lock()
        self.load_state()
        os.makedirs(f"logs_node_{self.node_id}", exist_ok=True)
        try:
            self.dump_file = open(f"logs_node_{self.node_id}/dump.txt", "a")
        except FileNotFoundError:
            self.dump_file = open(f"logs_node_{self.node_id}/dump.txt", "w")

    def write_to_dump_file(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.dump_file.write(log_message + "\n")
        self.dump_file.flush()

    def load_state(self):
        try:
            with open(f"logs_node_{self.node_id}/metadata.txt", "r") as f:
                self.commit_length = int(f.readline().strip())
                self.current_term = int(f.readline().strip())
                self.voted_for = f.readline().strip() or None

            with open(f"logs_node_{self.node_id}/logs.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split(" ")
                    if parts[0] == "NO-OP":
                        term = int(parts[1])
                        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=term))
                    elif parts[0] == "SET":
                        key = parts[1]
                        value = parts[2]
                        term = int(parts[3])
                        self.log.append(raft_pb2.LogEntry(operation="SET", key=key, value=value, term=term))
                        if len(self.log) <= self.commit_length:
                            self.data_store[key] = value
            
        except FileNotFoundError:
            pass

    def save_state(self):
        os.makedirs(f"logs_node_{self.node_id}", exist_ok=True)
        with open(f"logs_node_{self.node_id}/logs.txt", "w") as f:
            for entry in self.log:
                if entry.operation == "NO-OP":
                    f.write(f"NO-OP {entry.term}\n")
                elif entry.operation == "SET":
                    f.write(f"SET {entry.key} {entry.value} {entry.term}\n")
        with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
            f.write(f"{self.commit_length}\n")
            f.write(f"{self.current_term}\n")
            f.write(f"{self.voted_for or ''}\n")

    def start_election_timer(self):
        with self.timer_lock:
            election_timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
            self.election_timer = threading.Timer(election_timeout, self.start_election)
            self.election_timer.start()

    def start_heartbeat_timer(self):
        with self.timer_lock:
            self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.send_heartbeats)
            self.heartbeat_timer.start()

    def start_lease_timer(self):
        with self.timer_lock:
            self.lease_start_time = time.time()
            self.lease_timer = threading.Timer(LEASE_DURATION, self.lease_timeout)
            self.lease_timer.start()

    def cancel_election_timer(self):
        with self.timer_lock:
            if self.election_timer:
                self.election_timer.cancel()
                self.election_timer = None

    def cancel_heartbeat_timer(self):
        with self.timer_lock:
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()
                self.heartbeat_timer = None

    def cancel_lease_timer(self):
        with self.timer_lock:
            if self.lease_timer:
                self.lease_timer.cancel()
                self.lease_timer = None

    def start_election(self):
        # if self.state == LEADER:
        #     return
        self.write_to_dump_file(f"Node {self.node_id} election timer timed out, Starting election.")
        self.state = CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        last_term = 0
        if self.log:
            last_term = self.log[-1].term
        self.save_state()

        threads = []
        for node_id, node_address in self.node_addresses.items():
            if node_id != self.node_id:
                thread = self.request_vote_async(node_id, last_term)
                threads.append(thread)

        def check_election_result():
            if len(self.votes_received) >= (len(self.node_addresses) // 2) + 1:
                self.become_leader()
            else:
                self.start_election_timer()

        timer = threading.Timer(0.1, check_election_result)  # Adjust the duration as needed
        timer.start()
    
    def request_vote_async(self, node_id, last_term):
        def request_vote_task():
            with grpc.insecure_channel(self.node_addresses[node_id]) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                request = raft_pb2.RequestVoteArgs(
                    term=self.current_term,
                    candidate_id=self.node_id,
                    last_log_index=len(self.log),
                    last_log_term=last_term
                )
                try:
                    response = stub.RequestVote(request, timeout=1)
                    if response.vote_granted:
                        self.votes_received.add(node_id)
                        remaining_lease_duration = self.old_leader_lease_timeout - (time.time() - self.lease_start_time)
                        if remaining_lease_duration < 0:
                            remaining_lease_duration = 0
                        self.old_leader_lease_timeout = max(remaining_lease_duration, response.old_leader_lease_timeout)
                except grpc.RpcError as e:
                    self.write_to_dump_file(f"Error occurred while sending RPC to Node {node_id}.")

        thread = threading.Thread(target=request_vote_task)
        thread.start()
        return thread

    def become_leader(self):
        self.write_to_dump_file(f"Node {self.node_id} became the leader for term {self.current_term}.")
        self.state = LEADER
        self.current_leader = self.node_id
        self.votes_received = set()
        self.sent_length = {node_id: len(self.log) for node_id in self.node_addresses}
        self.acked_length = {node_id: 0 for node_id in self.node_addresses}
        # Cancel all existing timers as the node becomes a leader
        self.cancel_election_timer()
        self.cancel_heartbeat_timer()
        self.cancel_lease_timer()

        self.write_to_dump_file("New Leader waiting for Old Leader Lease to timeout.")
        time.sleep(self.old_leader_lease_timeout)

        self.start_lease_timer()
        self.append_no_op_entry()
        self.send_heartbeats()

    def lease_timeout(self):
        self.write_to_dump_file(f"Leader {self.node_id} lease renewal failed. Stepping Down.")
        self.step_down()

    def step_down(self):
        self.write_to_dump_file(f"{self.node_id} Stepping down")
        self.state = FOLLOWER
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}
        self.cancel_heartbeat_timer()
        self.cancel_lease_timer()
        self.cancel_election_timer()
        self.start_election_timer()

    def append_no_op_entry(self):
        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=self.current_term))
        self.save_state()

    def send_heartbeats(self):
        self.write_to_dump_file(f"Leader {self.node_id} sending heartbeat & Renewing Lease")

        threads = []
        #self.heartbeat_success_nodes = set()
        for node_id, node_address in self.node_addresses.items():
            if node_id != self.node_id:
                thread = self.replicate_log_async(node_id)
                threads.append(thread)

        # Check if the lease should be renewed
        if len(self.heartbeat_success_count) >= (len(self.node_addresses) // 2):
            self.write_to_dump_file("Lease renewed successfully.")
            self.lease_start_time = time.time()
            self.cancel_lease_timer()
            self.start_lease_timer()
            self.heartbeat_success_count = set()  # Reset the count after renewing the lease
        # else:
        #     self.write_to_dump_file("Lease not renewed yet.")

        # Ensure heartbeat continues
        self.start_heartbeat_timer()

    def replicate_log_async(self, follower_id):
        def replicate_log_task():
            with grpc.insecure_channel(self.node_addresses[follower_id]) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                prefix_len = self.sent_length.get(follower_id, 0)
                suffix = self.log[prefix_len:]
                prefix_term = 0
                if prefix_len > 0:
                    prefix_term = self.log[prefix_len - 1].term
                request = raft_pb2.AppendEntriesArgs(
                    term=self.current_term,
                    leader_id=self.node_id,
                    prev_log_index=prefix_len,
                    prev_log_term=prefix_term,
                    entries=suffix,
                    leader_commit=self.commit_length,
                    lease_duration=LEASE_DURATION
                )
                try:
                    response = stub.AppendEntries(request, timeout=1)
                    if response.success:
                        self.sent_length[follower_id] = prefix_len + len(suffix)
                        self.acked_length[follower_id] = prefix_len + len(suffix)
                        self.commit_log_entries()
                        self.heartbeat_success_count.add(follower_id)
                    else:
                        self.sent_length[follower_id] = max(0, self.sent_length.get(follower_id, 0) - 1)
                        self.replicate_log_async(follower_id)
                except grpc.RpcError as e:
                    self.write_to_dump_file(f"Error occurred while sending RPC to Node {follower_id}.")

        thread = threading.Thread(target=replicate_log_task)
        thread.start()
        return thread

    def commit_log_entries(self):
        min_acks = (len(self.node_addresses) // 2)
        ready = [index for index in range(1, len(self.log) + 1)
                 if len([node_id for node_id, acked_length in self.acked_length.items()
                         if acked_length >= index]) >= min_acks]
        if ready and max(ready) > self.commit_length and self.log[max(ready) - 1].term == self.current_term:
            for i in range(self.commit_length, max(ready)):
                entry = self.log[i]
                if entry.operation == "SET":
                    self.data_store[entry.key] = entry.value
                    self.write_to_dump_file(f"Node {self.node_id} (leader) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
            self.commit_length = max(ready)
            self.save_state()

    def RequestVote(self, request, context):
        if request.term > self.current_term:
            self.current_term = request.term
            self.voted_for = None
            self.save_state()
            self.step_down()

        if request.term == self.current_term:
            if self.voted_for is None or self.voted_for == request.candidate_id:
                last_term = 0
                if self.log:
                    last_term = self.log[-1].term
                log_ok = (request.last_log_term > last_term) or \
                         (request.last_log_term == last_term and request.last_log_index >= len(self.log))
                if log_ok:
                    self.voted_for = request.candidate_id
                    self.save_state()
                    self.write_to_dump_file(f"Vote granted for Node {request.candidate_id} in term {request.term}.")

                    remaining_lease_duration = self.old_leader_lease_timeout - (time.time() - self.lease_start_time)
                    if remaining_lease_duration < 0:
                        remaining_lease_duration = 0

                    return raft_pb2.RequestVoteReply(
                        term=self.current_term,
                        vote_granted=True,
                        old_leader_lease_timeout=remaining_lease_duration
                    )
                else:
                    self.write_to_dump_file(f"Vote denied for Node {request.candidate_id} in term {request.term}.")
                    return raft_pb2.RequestVoteReply(
                        term=self.current_term,
                        vote_granted=False,
                        old_leader_lease_timeout=self.old_leader_lease_timeout
                    )
            else:
                self.write_to_dump_file(f"Vote denied for Node {request.candidate_id} in term {request.term}.")
                return raft_pb2.RequestVoteReply(
                    term=self.current_term,
                    vote_granted=False,
                    old_leader_lease_timeout=self.old_leader_lease_timeout
                )
        else:
            self.write_to_dump_file(f"Vote denied for Node {request.candidate_id} in term {request.term}.")
            return raft_pb2.RequestVoteReply(
                term=self.current_term,
                vote_granted=False,
                old_leader_lease_timeout=self.old_leader_lease_timeout
            )

    def AppendEntries(self, request, context):
        if request.term > self.current_term:
            self.current_term = request.term
            self.voted_for = None
            self.save_state()
            self.step_down()

        if request.term == self.current_term:
            self.state = FOLLOWER
            self.current_leader = request.leader_id
            self.cancel_election_timer()
            self.old_leader_lease_timeout = request.lease_duration
            self.lease_start_time = time.time()
            self.start_election_timer()

        log_ok = (len(self.log) >= request.prev_log_index) and \
                (request.prev_log_index == 0 or self.log[request.prev_log_index - 1].term == request.prev_log_term)
        if request.term == self.current_term and log_ok:
            self.append_entries(request.prev_log_index, request.leader_commit, request.entries)
            ack = request.prev_log_index + len(request.entries)
            self.write_to_dump_file(f"Node {self.node_id} accepted AppendEntries RPC from {request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.current_term, success=True, ack=ack)
        else:
            self.write_to_dump_file(f"Node {self.node_id} rejected AppendEntries RPC from {request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.current_term, success=False, ack=0)

    def append_entries(self, prev_log_index, leader_commit, entries):
        if entries and len(self.log) > prev_log_index:
            index = min(len(self.log), prev_log_index + len(entries)) - 1
            if self.log[index].term != entries[index - prev_log_index].term:
                self.log = self.log[:prev_log_index]
        if prev_log_index + len(entries) > len(self.log):
            self.log.extend(entries[len(self.log) - prev_log_index:])
        if leader_commit > self.commit_length:
            for i in range(self.commit_length, leader_commit):
                entry = self.log[i]
                if entry.operation == "SET":
                    self.data_store[entry.key] = entry.value
                    self.write_to_dump_file(f"Node {self.node_id} (follower) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
            self.commit_length = leader_commit
        self.save_state()

    def ServeClient(self, request, context):
        if self.state == LEADER:
            parts = request.Request.split()
            if parts[0] == "GET":
                key = parts[1]
                value = self.data_store.get(key, "")
                return raft_pb2.ServeClientReply(Data=value, LeaderID=str(self.node_id), Success=True)
            
            elif parts[0] == "SET":
                key = parts[1]
                value = parts[2]
                log_entry = raft_pb2.LogEntry(operation="SET", key=key, value=value, term=self.current_term)
                self.log.append(log_entry)
                self.save_state()

                # Wait for the entry to be committed
                while self.commit_length < len(self.log):
                    time.sleep(0.1)  # Adjust the sleep duration as needed

                # Check if the committed entry matches the appended entry
                if self.log[self.commit_length - 1] == log_entry:
                    return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.node_id), Success=True)
                else:
                    return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.node_id), Success=False)
        else:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.current_leader), Success=False)

def signal_handler(sig, frame):
    print("Received SIGINT signal. Exiting gracefully...")
    # Stop all timers
    node.save_state()
    node.cancel_election_timer()
    node.cancel_heartbeat_timer()
    node.cancel_lease_timer()
    sys.exit(0)

def serve(node_id, node_addresses):
    global node  # Make the node object accessible to the signal_handler
    node = RaftNode(node_id, node_addresses)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(node, server)
    server.add_insecure_port(node_addresses[node_id])
    server.start()
    print(f"Node {node_id} started.")
    node.start_election_timer()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Exiting gracefully...")
        server.stop(0)

def main():
    if len(sys.argv) < 2:
        print("Usage: python raft.py <node_id>")
        sys.exit(1)
    node_id = int(sys.argv[1])
    node_addresses = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
    }
    signal.signal(signal.SIGINT, signal_handler)
    serve(node_id, node_addresses)

if __name__ == "__main__":
    main()

# TODO
""" 
1. (partially done, testing needed) handle the case when the leader should respond success to the client only after the entry has been committed on the leader.
2. (done) log and metadata retireval when the node is started again (i think only logs are retrieved and not data_store, so thats why right now nothing is retrived if we do a get request?)     
3. (done?) check if lease time stuff is working properly (assignment test case no. 4)       
4. (done) When print(f"Error occurred while sending RPC to Node {node_id}.") [at two places in the code] happens, it takes extra time in the heartbeat, and the heartbeat doesnt go to all nodes simultaniously and via non blocking calls. Need to do such that RPC is sent simultaniously to all nodes instead of using a for loop.
5. (no, done) Should leader wait for acks from the followers everytime he sends a heartbeat, in order to confirm his leadership?
6. When we do a SET operation, then the election and lease timers get messed up and started up somehow in the leader, seems like they do not appear to get cancelled. Need to check.
"""