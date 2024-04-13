# master.py
import grpc
import kmeans_pb2
import kmeans_pb2_grpc
import random
import os
import math
import time
import shutil

def create_grpc_stubs(num, base_port, stub_class):
    stubs = []
    for i in range(num):
        channel = grpc.insecure_channel(f'localhost:{base_port + i}')
        stub = stub_class(channel)
        stubs.append(stub)
    return stubs

def run_master(num_mappers, num_reducers, num_centroids, num_iterations, max_retries=5):
    

    # Initialize centroids randomly from input data points
    centroids = initialize_centroids(num_centroids)
    input_splits = split_input_data(num_mappers)
    
    iteration = 0
    while True:
        # Delete the directories if they exist
        for directory in ["Mappers", "Reducers"]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        
        print(f"Iteration {iteration + 1}")
        
        # Invoke mappers
        print("Invoking Mappers...")
        mapper_stubs = create_grpc_stubs(num_mappers, 50051, kmeans_pb2_grpc.MapperStub)
            
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
        failed_mappers = set()
        while len(mapper_responses) < num_mappers:
            for i, (stub, request) in enumerate(zip(mapper_stubs, mapper_requests)):
                if i not in [m[0] for m in mapper_responses] and i not in failed_mappers:
                    try:
                        response = stub.Map(request)
                        if response.status == "SUCCESS":
                            mapper_responses.append((i, response))
                            print(f"Mapper ID {request.mapper_id} response: {response.status}")
                        elif response.status == "FAILED":
                            failed_mappers.add(i)
                            print(f"Mapper ID {request.mapper_id} failed")
                    except grpc.RpcError as e:
                        failed_mappers.add(i)
                        print(f"Mapper ID {request.mapper_id} failed because of gRPC error")
                        # reset stubs

            if failed_mappers:
                # Reassign failed mapper tasks to available mappers or completed mappers
                available_mappers = set(range(num_mappers)) - failed_mappers
                for i in failed_mappers.copy():
                    if available_mappers:
                        new_mapper_id = random.choice(list(available_mappers) + [i]) # Reassign to any other available mapper or the same mapper
                        request = mapper_requests[i]
                        stub = mapper_stubs[new_mapper_id]
                        try:
                            response = stub.Map(request)
                            if response.status == "SUCCESS":
                                mapper_responses.append((i, response))
                                print(f"Reassigned Mapper ID {i} to Mapper ID {new_mapper_id}")
                                failed_mappers.remove(i)
                            elif response.status == "FAILED":
                                print(f"Reassigned Mapper ID {new_mapper_id} failed")
                        except grpc.RpcError as e:
                            print(f"Reassigned Mapper ID {new_mapper_id} failed because of gRPC error")
                    else:
                        try:
                            raise Exception("All mappers failed...retrying from start")
                        except Exception as e:
                            print(e)
                            #time.sleep(5)
                            failed_mappers = set()

                            mapper_stubs = create_grpc_stubs(num_mappers, 50051, kmeans_pb2_grpc.MapperStub)                              
                            break                            

        # Invoke reducers
        print("Invoking Reducers...")
        reducer_stubs = create_grpc_stubs(num_reducers, 60051, kmeans_pb2_grpc.ReducerStub)

        reducer_requests = []
        for i in range(num_reducers):
            request = kmeans_pb2.ReducerRequest(
                reducer_id=i,
                num_mappers=num_mappers
            )
            reducer_requests.append(request)

        reducer_responses = []
        failed_reducers = set()
        while len(reducer_responses) < num_centroids:
            for i, (stub, request) in enumerate(zip(reducer_stubs, reducer_requests)):
                if i not in [r[0] for r in reducer_responses] and i not in failed_reducers:
                    try:
                        responses = stub.Reduce(request)
                        success = False
                        for response in responses:
                            if response.status == "SUCCESS" or response.status == "NO_TASKS":
                                success = True
                                if response.status == "SUCCESS":
                                    reducer_responses.append((i, response))
                                print(f"Reducer ID {request.reducer_id} response: {response.status}")
                            elif response.status == "FAILED":
                                failed_reducers.add(i)
                                print(f"Reducer ID {request.reducer_id} failed")
                                break
                        if not success:
                            failed_reducers.add(i)
                    except grpc.RpcError as e:
                        failed_reducers.add(i)
                        print(f"Reducer ID {request.reducer_id} failed because of gRPC error")

            if failed_reducers:
                # Reassign failed reducer tasks to available reducers or completed reducers
                available_reducers = set(range(num_reducers)) - failed_reducers
                for i in failed_reducers.copy():
                    if available_reducers:
                        new_reducer_id = random.choice(list(available_reducers) + [i]) # Reassign to any other available reducer or the same reducer
                        request = reducer_requests[i]
                        stub = reducer_stubs[new_reducer_id]
                        try:
                            responses = stub.Reduce(request)
                            success = False
                            for response in responses:
                                if response.status == "SUCCESS" or response.status == "NO_TASKS":
                                    success = True
                                    if response.status == "SUCCESS":
                                        reducer_responses.append((i, response))
                                    if i in failed_reducers:
                                        failed_reducers.remove(i)
                                    print(f"Reassigned Reducer ID {i} to Reducer ID {new_reducer_id}")
                                elif response.status == "FAILED":
                                    print(f"Reassigned Reducer ID {new_reducer_id} failed")
                                    break
                            if not success:
                                pass
                        except grpc.RpcError as e:
                            print(f"Reassigned Reducer ID {new_reducer_id} failed because of gRPC error")
                    else:
                        try:
                            raise Exception("All reducers failed...retrying from start")
                        except Exception as e:
                            print(e)
                            #time.sleep(5)
                            failed_reducers = set()

                            reducer_stubs = create_grpc_stubs(num_reducers, 60051, kmeans_pb2_grpc.ReducerStub)
                            break
                        

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
    num_iterations = 50
    
    run_master(num_mappers, num_reducers, num_centroids, num_iterations)
        