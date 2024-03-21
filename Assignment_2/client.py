import grpc
import raft_pb2
import raft_pb2_grpc
import signal
import os

def signal_handler(signal, frame):
    print("\nProgram exiting gracefully")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

def run_client(node_addresses):
    leader_id = None
    while True:
        leader_found = False
        if leader_id is None:
            for node_id, node_address in node_addresses.items():
                with grpc.insecure_channel(node_address) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    try:
                        response = stub.ServeClient(raft_pb2.ServeClientArgs(Request="GET __leader__"), timeout=5)
                        if response.Success:
                            leader_id = response.LeaderID
                            print(f"Connected to leader: {leader_id}")
                            leader_found = True
                            break
                    except grpc.RpcError as e:
                        print("Leader is unavailable. Trying again...")
                        continue
            if not leader_found:
                print("No leader found in the network. Exiting.")
                return
        else:
            try:
                with grpc.insecure_channel(node_addresses[int(leader_id)]) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    while True:
                        request = input("Enter command (GET <key> or SET <key> <value>): ")
                        try:
                            response = stub.ServeClient(raft_pb2.ServeClientArgs(Request=request), timeout=5)
                            if response.Success:
                                print(f"Response: {response.Data}")
                            else:
                                print(f"Leader changed. Connecting to new leader...")
                                leader_id = response.LeaderID
                                break
                        except grpc.RpcError as e:
                            print("Leader is unavailable. Trying again...")
                            leader_id = None
                            break
            except:
                leader_id = None

if __name__ == "__main__":
    node_addresses = {
        0: "10.190.0.2:50050",
        1: "10.190.0.3:50051",
        2: "10.190.0.4:50052",
        3: "10.190.0.5:50053",
        4: "10.190.0.6:50054",
    }
    try:
        run_client(node_addresses)
    except SystemExit:
        pass