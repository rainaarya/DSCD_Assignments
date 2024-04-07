# master.py
import grpc
import kmeans_pb2
import kmeans_pb2_grpc
import random
import os
import math

def run_master(num_mappers, num_reducers, num_centroids, num_iterations):
    # Initialize centroids randomly from input data points
    centroids = initialize_centroids(num_centroids)
    input_splits = split_input_data(num_mappers)
    
    iteration = 0
    while True:
        print(f"Iteration {iteration + 1}")
        
        # Invoke mappers
        print("Invoking Mappers...")
        mapper_stubs = []
        for i in range(num_mappers):
            channel = grpc.insecure_channel(f'localhost:{50051 + i}')
            stub = kmeans_pb2_grpc.MapperStub(channel)
            mapper_stubs.append(stub)
            
        mapper_requests = []
        for i in range(num_mappers):
            input_split_str = ''.join(input_splits[i])  # Serialize input split to string
            request = kmeans_pb2.MapperRequest(
                mapper_id=i,
                centroids=centroids,
                input_split=input_split_str
            )
            mapper_requests.append(request)
        
        mapper_responses = []
        for stub, request in zip(mapper_stubs, mapper_requests):
            response = stub.Map(request)
            mapper_responses.append(response)
            print(f"Mapper {request.mapper_id} response: {response.status}")
        
        # Invoke reducers
        print("Invoking Reducers...")
        reducer_stubs = []
        for i in range(num_reducers):
            channel = grpc.insecure_channel(f'localhost:{60051 + i}')
            stub = kmeans_pb2_grpc.ReducerStub(channel)
            reducer_stubs.append(stub)
        
        reducer_requests = []
        for i in range(num_reducers):
            request = kmeans_pb2.ReducerRequest(
                reducer_id=i,
                num_mappers=num_mappers
            )
            reducer_requests.append(request)
        
        reducer_responses = []
        for stub, request in zip(reducer_stubs, reducer_requests):
            response = stub.Reduce(request)
            reducer_responses.append(response)
            print(f"Reducer {request.reducer_id} response: {response.status}")
        
        # Compile centroids
        print("Compiling centroids...")
        updated_centroids = compile_centroids(reducer_responses)
        
        print("Updated centroids:")
        for centroid in updated_centroids:
            print(centroid)
        
        if has_converged(centroids, updated_centroids) or iteration + 1 == num_iterations:
            centroids = updated_centroids
            break
        
        centroids = updated_centroids
        iteration += 1
    
    # Save final centroids
    with open("centroids.txt", "w") as file:
        for centroid in centroids:
            file.write(f"{centroid.x},{centroid.y}\n")
    
    print("K-means clustering completed.")

def has_converged(prev_centroids, curr_centroids, threshold=1e-4):
    for prev_centroid, curr_centroid in zip(prev_centroids, curr_centroids):
        if euclidean_distance(prev_centroid, curr_centroid) > threshold:
            return False
    return True

def euclidean_distance(centroid1, centroid2):
    return math.sqrt((centroid1.x - centroid2.x) ** 2 + (centroid1.y - centroid2.y) ** 2)

def initialize_centroids(num_centroids):
    centroids = []
    with open("Input/points.txt", "r") as file:
        lines = file.readlines()
        random_indices = random.sample(range(len(lines)), num_centroids)
        for index in random_indices:
            point = lines[index].strip().split(",")
            centroid = kmeans_pb2.Centroid(x=float(point[0]), y=float(point[1]))
            centroids.append(centroid)
    return centroids

def compile_centroids(reducer_responses):
    centroids = []
    for response in reducer_responses:
        centroid = kmeans_pb2.Centroid(x=response.centroid_x, y=response.centroid_y)
        centroids.append(centroid)
    return centroids

def split_input_data(num_mappers):
    input_splits = []
    with open("Input/points.txt", "r") as file:
        lines = file.readlines()
        chunk_size = len(lines) // num_mappers
        for i in range(num_mappers):
            start = i * chunk_size
            end = start + chunk_size
            if i == num_mappers - 1:
                end = len(lines)
            input_splits.append(lines[start:end])
    return input_splits

if __name__ == "__main__":
    num_mappers = 3
    num_reducers = 2
    num_centroids = 2
    num_iterations = 5
    
    run_master(num_mappers, num_reducers, num_centroids, num_iterations)