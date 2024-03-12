import grpc
import raft_pb2
import raft_pb2_grpc

def run_client(node_addresses):
    leader_id = None
    while True:
        leader_found = False
        if leader_id is None:
            for node_id, node_address in node_addresses.items():
                with grpc.insecure_channel(node_address) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    try:
                        response = stub.ServeClient(raft_pb2.ServeClientArgs(Request="GET __leader__"))
                        if response.Success:
                            leader_id = response.LeaderID
                            print(f"Connected to leader: {leader_id}")
                            leader_found = True
                            break
                    except grpc.RpcError as e:
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
            except:
                leader_id = None

if __name__ == "__main__":
    node_addresses = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
        5: "localhost:50055",
    }
    run_client(node_addresses)