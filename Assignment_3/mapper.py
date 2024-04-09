# mapper.py
import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import math
import os

class MapperServicer(kmeans_pb2_grpc.MapperServicer):
    def Map(self, request, context):
        mapper_id = request.mapper_id
        centroids = request.centroids
        input_split = request.input_split
        num_reducers = request.num_reducers
        
        # Read input split
        data_points = self.read_input_split(input_split)
        
        # Map data points to nearest centroids
        mapped_data = self.map_data_points(data_points, centroids)
        
        # Partition mapped data
        partitioned_data = self.partition_data(mapped_data, num_reducers)
        
        # Save partitioned data
        self.save_partitioned_data(partitioned_data, mapper_id)
        
        return kmeans_pb2.MapperResponse(status="SUCCESS")

    def GetPartitionData(self, request, context):
        mapper_id = request.mapper_id
        reducer_id = request.reducer_id
        
        file_path = f"Mappers/M{mapper_id + 1}/partition_{reducer_id + 1}.txt"
        partition_data = []
        
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                for line in file:
                    data = line.strip().split(",")
                    centroid_id = int(data[0])
                    point = kmeans_pb2.Point(x=float(data[1]), y=float(data[2]))
                    partition_data.append(kmeans_pb2.PartitionData(centroid_id=centroid_id, point=point))
        
        return kmeans_pb2.PartitionDataResponse(partition_data=partition_data)
    
    def read_input_split(self, input_split):
        data_points = []
        lines = input_split.split('\n')  # Split input split string into lines
        for line in lines:
            if line.strip():  # Skip empty lines
                point = line.strip().split(",")
                data_points.append((float(point[0]), float(point[1])))
        return data_points
    
    def map_data_points(self, data_points, centroids):
        mapped_data = {}
        for point in data_points:
            min_distance = float("inf")
            nearest_centroid = None
            for i, centroid in enumerate(centroids):
                distance = self.euclidean_distance(point, centroid)
                if distance < min_distance:
                    min_distance = distance
                    nearest_centroid = i
            if nearest_centroid not in mapped_data:
                mapped_data[nearest_centroid] = []
            mapped_data[nearest_centroid].append(point)
        return mapped_data
    
    def euclidean_distance(self, point, centroid):
        return math.sqrt((point[0] - centroid.x)**2 + (point[1] - centroid.y)**2)
    
    def partition_data(self, mapped_data, num_reducers):
        partitioned_data = {}
        for centroid_id, data_points in mapped_data.items():
            reducer_id = centroid_id % num_reducers
            if reducer_id not in partitioned_data:
                partitioned_data[reducer_id] = {}
            partitioned_data[reducer_id][centroid_id] = data_points
        return partitioned_data
    
    def save_partitioned_data(self, partitioned_data, mapper_id):
        for reducer_id, data in partitioned_data.items():
            directory = f"Mappers/M{mapper_id + 1}"
            os.makedirs(directory, exist_ok=True)
            file_path = f"{directory}/partition_{reducer_id + 1}.txt"
            with open(file_path, "w") as file:
                for centroid_id, data_points in data.items():
                    for point in data_points:
                        file.write(f"{centroid_id},{point[0]},{point[1]}\n")

def serve():
    try:
        port = input("Please enter the port number: ")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        kmeans_pb2_grpc.add_MapperServicer_to_server(MapperServicer(), server)
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Interrupt received, stopping server...")
        server.stop(0)
        print("Server stopped.")

if __name__ == "__main__":
    serve()