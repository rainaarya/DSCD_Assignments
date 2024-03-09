import grpc
import raft_pb2
import raft_pb2_grpc

def run_client(node_addresses):
    leader_id = None
    while True:
        if leader_id is None:
            for node_id, node_address in node_addresses.items():
                with grpc.insecure_channel(node_address) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    try:
                        response = stub.ServeClient(raft_pb2.ServeClientArgs(Request="GET __leader__"))
                        if response.Success:
                            leader_id = response.LeaderID
                            print(f"Connected to leader: {leader_id}")
                            break
                    except grpc.RpcError as e:
                        continue
        else:
            with grpc.insecure_channel(node_addresses[int(leader_id)]) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                while True:
                    request = input("Enter command (GET <key> or SET <key> <value>): ")
                    try:
                        response = stub.ServeClient(raft_pb2.ServeClientArgs(Request=request))
                        if response.Success:
                            print(f"Response: {response.Data}")
                        else:
                            print(f"Leader changed. Connecting to new leader.")
                            leader_id = response.LeaderID
                            break
                    except grpc.RpcError as e:
                        print(f"Error occurred: {e}")
                        leader_id = None
                        break

if __name__ == "__main__":
    node_addresses = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052"
    }
    run_client(node_addresses)