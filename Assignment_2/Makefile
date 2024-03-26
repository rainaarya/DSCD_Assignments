all:
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

clean:
	rm -rf raft_pb2.py raft_pb2_grpc.py logs_node_*
