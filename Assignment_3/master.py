# master.py
import grpc
import kmeans_pb2
import kmeans_pb2_grpc
import random
import os
import math
import time

def run_master(num_mappers, num_reducers, num_centroids, num_iterations, max_retries=5):
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
            input_split_str = f"{input_splits[i][0]},{input_splits[i][1]}"  # Serialize input split range to string
            request = kmeans_pb2.MapperRequest(
                mapper_id=i,
                centroids=centroids,
                input_split=input_split_str,
                num_reducers=num_reducers
            )
            mapper_requests.append(request)

        mapper_responses = []
        mapper_retries = {}
        while len(mapper_responses) < num_mappers:
            for i, (stub, request) in enumerate(zip(mapper_stubs, mapper_requests)):
                if i not in [m[0] for m in mapper_responses]:
                    try:
                        response = stub.Map(request)
                        mapper_responses.append((i, response))
                        print(f"Mapper {request.mapper_id} response: {response.status}")
                    except grpc.RpcError as e:
                        print(f"Mapper {request.mapper_id} failed")
                        if i not in mapper_retries:
                            mapper_retries[i] = 0
                        mapper_retries[i] += 1
                        if mapper_retries[i] <= max_retries:
                            print(f"Retrying Mapper {request.mapper_id}...")
                            # Recreate the channel and stub for the failed mapper
                            channel = grpc.insecure_channel(f'localhost:{50051 + i}')
                            stub = kmeans_pb2_grpc.MapperStub(channel)
                            mapper_stubs[i] = stub
                            time.sleep(1)  # Wait before retrying
                        else:
                            raise Exception(f"Mapper {request.mapper_id} failed after {max_retries} retries")        
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
        reducer_retries = {}
        while len(reducer_responses) < num_reducers:
            for i, (stub, request) in enumerate(zip(reducer_stubs, reducer_requests)):
                if i not in [r[0] for r in reducer_responses]:
                    try:
                        responses = stub.Reduce(request)
                        for response in responses:
                            reducer_responses.append((i, response))
                            print(f"Reducer {request.reducer_id} response: {response.status}")
                    except grpc.RpcError as e:
                        print(f"Reducer {request.reducer_id} failed")
                        if i not in reducer_retries:
                            reducer_retries[i] = 0
                        reducer_retries[i] += 1
                        if reducer_retries[i] <= max_retries:
                            print(f"Retrying Reducer {request.reducer_id}...")
                            # Recreate the channel and stub for the failed reducer
                            channel = grpc.insecure_channel(f'localhost:{60051 + i}')
                            stub = kmeans_pb2_grpc.ReducerStub(channel)
                            reducer_stubs[i] = stub
                            time.sleep(1)  # Wait before retrying
                        else:
                            raise Exception(f"Reducer {request.reducer_id} failed after {max_retries} retries")        
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
    if len(prev_centroids) != len(curr_centroids):
        return False

    prev_centroids = sorted(prev_centroids, key=lambda c: (c.x, c.y))
    curr_centroids = sorted(curr_centroids, key=lambda c: (c.x, c.y))

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
    centroids = {}
    for reducer_id, response in reducer_responses:
        if response.status == "NO_TASKS":
            continue
        centroid_id = response.centroid_id
        centroid = kmeans_pb2.Centroid(x=response.centroid_x, y=response.centroid_y)
        centroids[centroid_id] = centroid
    return list(centroids.values())

def split_input_data(num_mappers):
    input_splits = []
    with open("Input/points.txt", "r") as file:
        num_lines = sum(1 for line in file)
        chunk_size = num_lines // num_mappers
        for i in range(num_mappers):
            start = i * chunk_size
            end = start + chunk_size
            if i == num_mappers - 1:
                end = num_lines
            input_splits.append((start, end))
    return input_splits

if __name__ == "__main__":
    num_mappers = 3
    num_reducers = 3
    num_centroids = 3
    num_iterations = 100
    
    try:
        run_master(num_mappers, num_reducers, num_centroids, num_iterations)
    except Exception as e:
        print(e)