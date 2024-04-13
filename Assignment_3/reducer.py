# reducer.py
import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import os
import random

class ReducerServicer(kmeans_pb2_grpc.ReducerServicer):

    def __init__(self, my_reducer_id):
        self.my_reducer_id = my_reducer_id

    def Reduce(self, request, context):
        reducer_id = request.reducer_id
        num_mappers = request.num_mappers

        # Shuffle and sort data
        shuffled_data = self.shuffle_data(reducer_id, num_mappers)

        # Reduce data
        reduced_data = self.reduce_data(shuffled_data)

        # Simulate failure with a probability of 0.2
        if random.random() < 0.2:
            yield kmeans_pb2.ReducerResponse(status="FAILED")
            return

        # Save reduced data
        self.save_reduced_data(reduced_data, reducer_id, self.my_reducer_id)

        for data in reduced_data:
            if data:
                yield kmeans_pb2.ReducerResponse(
                    status="SUCCESS",
                    centroid_id=data[0],
                    centroid_x=data[1][0],
                    centroid_y=data[1][1]
                )
        if not reduced_data:
            yield kmeans_pb2.ReducerResponse(status="NO_TASKS")

    def shuffle_data(self, reducer_id, num_mappers):
        shuffled_data = {}
        for mapper_id in range(num_mappers):
            try:
                channel = grpc.insecure_channel(f'localhost:{50051 + mapper_id}')
                stub = kmeans_pb2_grpc.MapperStub(channel)
                request = kmeans_pb2.PartitionDataRequest(mapper_id=mapper_id, reducer_id=reducer_id)
                response = stub.GetPartitionData(request, timeout=0.3)
                
                for partition_data in response.partition_data:
                    centroid_id = partition_data.centroid_id
                    point = (partition_data.point.x, partition_data.point.y)
                    if centroid_id not in shuffled_data:
                        shuffled_data[centroid_id] = []
                    shuffled_data[centroid_id].append(point)
            except grpc.RpcError as e:
                continue
    
        return shuffled_data
    
    def reduce_data(self, shuffled_data):
        reduced_data = []
        for centroid_id, data_points in shuffled_data.items():
            sum_x = sum(point[0] for point in data_points)
            sum_y = sum(point[1] for point in data_points)
            count = len(data_points)
            new_centroid = (centroid_id, (sum_x / count, sum_y / count))
            reduced_data.append(new_centroid)
        return reduced_data
    
    def save_reduced_data(self, reduced_data, reducer_id, my_reducer_id):
        directory = "Reducers"
        os.makedirs(directory, exist_ok=True)  # Create the directory if it doesn't exist
        file_path = f"{directory}/R{my_reducer_id + 1}.txt"        
        mode = "w" if reducer_id == my_reducer_id else "a"        
        with open(file_path, mode) as file:
            for data in reduced_data:
                if data:
                    file.write(f"{data[0]},{data[1][0]},{data[1][1]}\n")

def serve():
    try:
        port = input("Please enter the port number: ")
        my_reducer_id = int(port) - 60051
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        kmeans_pb2_grpc.add_ReducerServicer_to_server(ReducerServicer(my_reducer_id), server)
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Interrupt received, stopping server...")
        server.stop(0)
        print("Server stopped.")

if __name__ == "__main__":
    serve()