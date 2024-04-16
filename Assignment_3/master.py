# master.py
import grpc
import kmeans_pb2
import kmeans_pb2_grpc
import random
import os
import math
import time
import shutil
import concurrent.futures

def log_message(message):
    print(message)
    with open("dump.txt", "a") as file:
        file.write(message + "\n")

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
    
    log_message("Randomly initialized centroids:")
    for centroid in centroids:
        log_message(f"({centroid.x}, {centroid.y})")
    
    iteration = 0
    while True:
        # Delete the directories if they exist
        for directory in ["Mappers", "Reducers"]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        
        log_message(f"\nIteration {iteration + 1}")
        
        # Invoke mappers
        log_message("Invoking Mappers...")
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

        def map_request(i, stub, request, failed_task=False):
            if not failed_task:
                log_message(f"Executing gRPC call to Mapper ID {i}")
            try:
                response = stub.Map(request)
                return (i, response)
            except grpc.RpcError as e:
                return (i, e)
            
        mapper_responses = []
        failed_mappers = set()
        while len(mapper_responses) < num_mappers:
            futures = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for i, (stub, request) in enumerate(zip(mapper_stubs, mapper_requests)):
                    if i not in [m[0] for m in mapper_responses] and i not in failed_mappers:
                        futures.append(executor.submit(map_request, i, stub, request))
                for future in concurrent.futures.as_completed(futures):
                    i, response = future.result()                       
                    if isinstance(response, grpc.RpcError):
                        failed_mappers.add(i)
                        log_message(f"Mapper ID {i} failed because of gRPC error")
                    else:
                        if response.status == "SUCCESS":
                            mapper_responses.append((i, response))
                            log_message(f"Mapper ID {i} response: {response.status}")
                        elif response.status == "FAILED":
                            failed_mappers.add(i)
                            log_message(f"Mapper ID {i} response: {response.status}")

            if failed_mappers:
                # Reassign failed mapper tasks to available mappers or completed mappers
                available_mappers = set(range(num_mappers)) - failed_mappers
                futures = []
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for i in failed_mappers.copy():
                        if available_mappers:
                            new_mapper_id = random.choice(list(available_mappers) + [i]) # Reassign to any other available mapper or the same mapper
                            request = mapper_requests[i]
                            stub = mapper_stubs[new_mapper_id]
                            log_message(f"Executing gRPC call to Mapper ID {new_mapper_id} for mapping task of Mapper ID {i}")
                            futures.append(executor.submit(map_request, i, stub, request, failed_task=True))
                        else:
                            try:
                                raise Exception("All mappers failed...retrying")
                            except Exception as e:
                                log_message(str(e))
                                failed_mappers = set()
                                mapper_stubs = create_grpc_stubs(num_mappers, 50051, kmeans_pb2_grpc.MapperStub)
                                break
                
                    for future in concurrent.futures.as_completed(futures):
                        i, response = future.result()
                        if isinstance(response, grpc.RpcError):
                            log_message(f"Reassigned Mapper ID {i} task to Mapper ID {new_mapper_id} FAILED because of gRPC error")
                        else:
                            if response.status == "SUCCESS":
                                mapper_responses.append((i, response))
                                log_message(f"Reassigned Mapper ID {i} task to Mapper ID {new_mapper_id}: SUCCESS")
                                failed_mappers.remove(i)
                            elif response.status == "FAILED":
                                log_message(f"Reassigned Mapper ID {i} task to Mapper ID {new_mapper_id}: FAILED")
            
        # Invoke reducers
        log_message("\nInvoking Reducers...")
        reducer_stubs = create_grpc_stubs(num_reducers, 60051, kmeans_pb2_grpc.ReducerStub)

        reducer_requests = []
        for i in range(num_reducers):
            request = kmeans_pb2.ReducerRequest(
                reducer_id=i,
                num_mappers=num_mappers
            )
            reducer_requests.append(request)


        def reduce_request(i, stub, request, failed_task=False):
            if not failed_task:
                log_message(f"Executing gRPC call to Reducer ID {i}")
            try:
                responses = stub.Reduce(request)
                return (i, responses)
            except grpc.RpcError as e:
                return (i, e)


        reducer_responses = []
        reducer_no_tasks = []
        failed_reducers = set()
        while len(reducer_responses) < num_centroids:
            futures = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for i, (stub, request) in enumerate(zip(reducer_stubs, reducer_requests)):
                    if i not in [r[0] for r in reducer_responses] and i not in failed_reducers and i not in reducer_no_tasks:
                        futures.append(executor.submit(reduce_request, i, stub, request))
                for future in concurrent.futures.as_completed(futures):
                    i, responses = future.result()
                    try:
                        success = False
                        counter = 0
                        for response in responses:
                            counter += 1
                            if response.status == "SUCCESS" or response.status == "NO_TASKS":
                                success = True
                                if response.status == "SUCCESS":
                                    reducer_responses.append((i, response))
                                if response.status == "NO_TASKS":
                                    reducer_no_tasks.append(i)
                                if counter > 1:
                                    log_message(f"Reducer ID {i} response {counter}: {response.status}")
                                else:
                                    log_message(f"Reducer ID {i} response: {response.status}")
                            elif response.status == "FAILED":
                                failed_reducers.add(i)
                                if counter > 1:
                                    log_message(f"Reducer ID {i} response {counter}: {response.status}")
                                else:
                                    log_message(f"Reducer ID {i} response: {response.status}")
                                break
                        if not success:
                            failed_reducers.add(i)
                    except grpc.RpcError as e:
                        failed_reducers.add(i)
                        log_message(f"Reducer ID {i} failed because of gRPC error")

            if failed_reducers:
                # Reassign failed reducer tasks to available reducers or completed reducers
                available_reducers = set(range(num_reducers)) - failed_reducers
                futures = []
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for i in failed_reducers.copy():
                        if available_reducers:
                            new_reducer_id = random.choice(list(available_reducers) + [i]) # Reassign to any other available reducer or the same reducer
                            request = reducer_requests[i]
                            stub = reducer_stubs[new_reducer_id]
                            log_message(f"Executing gRPC call to Reducer ID {new_reducer_id} for reducing task of Reducer ID {i}")
                            futures.append(executor.submit(reduce_request, i, stub, request, failed_task=True))
                        else:
                            try:
                                raise Exception("All reducers failed...retrying")
                            except Exception as e:
                                log_message(str(e))
                                failed_reducers = set()
                                reducer_stubs = create_grpc_stubs(num_reducers, 60051, kmeans_pb2_grpc.ReducerStub)
                                break
                
                    for future in concurrent.futures.as_completed(futures):
                        i, responses = future.result()
                        try:
                            success = False
                            for response in responses:
                                if response.status == "SUCCESS" or response.status == "NO_TASKS":
                                    success = True
                                    if response.status == "SUCCESS":
                                        reducer_responses.append((i, response))
                                    if response.status == "NO_TASKS":
                                        reducer_no_tasks.append(i)
                                    if i in failed_reducers:
                                        failed_reducers.remove(i)
                                    log_message(f"Reassigned Reducer ID {i} task to Reducer ID {new_reducer_id}: {response.status}")
                                elif response.status == "FAILED":
                                    log_message(f"Reassigned Reducer ID {i} task to Reducer ID {new_reducer_id}: FAILED")
                                    break
                            if not success:
                                pass
                        except grpc.RpcError as e:
                            log_message(f"Reassigned Reducer ID {i} task to Reducer ID {new_reducer_id} FAILED because of gRPC error")
                        

        # Compile centroids
        log_message("\nCompiling centroids...")
        updated_centroids = compile_centroids(reducer_responses)
        
        log_message("Updated centroids:")
        for centroid in updated_centroids:
            log_message(f"({centroid.x}, {centroid.y})")
        
        if has_converged(centroids, updated_centroids) or iteration + 1 == num_iterations:
            centroids = updated_centroids
            break
        
        centroids = updated_centroids
        iteration += 1
    
    # Save final centroids
    with open("centroids.txt", "w") as file:
        for centroid in centroids:
            file.write(f"{centroid.x},{centroid.y}\n")
    
    log_message("K-means clustering completed.")

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
    num_mappers = int(input("Enter the number of mappers: "))
    num_reducers = int(input("Enter the number of reducers: "))
    num_centroids = int(input("Enter the number of centroids: "))
    num_iterations = 50
    
    # clear the contents of the file dump.txt
    with open("dump.txt", "w") as file:
        file.write("")
    run_master(num_mappers, num_reducers, num_centroids, num_iterations)