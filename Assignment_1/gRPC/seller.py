import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import uuid
import threading
from concurrent import futures
import os
import time

class SellerClient:
    def __init__(self, server_address, notificationPort):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.uuid = str(uuid.uuid1())
        self.notificationPort = notificationPort
        #self.address = buyer_address

    def register_seller(self):
        response = self.stub.RegisterSeller(
            marketplace_pb2.SellerRegistration(uuid=self.uuid, notificationPort=self.notificationPort)
        )
        print(response.message)

    def sell_item(self, name, category, quantity, description, price):
        item = marketplace_pb2.Item(
            name=name, 
            category=category, 
            quantity=quantity, 
            description=description, 
            price=price
        )
        response = self.stub.SellItem(
            marketplace_pb2.ItemManagement(uuid=self.uuid, item=item)
        )
        print(response.message)

    def update_item(self, item_id, new_quantity, new_price):
        item = marketplace_pb2.Item(
            id=item_id, quantity=new_quantity, price=new_price
        )
        response = self.stub.UpdateItem(
            marketplace_pb2.ItemManagement(uuid=self.uuid, item=item)
        )
        print(response.message)

    def delete_item(self, item_id):
        item = marketplace_pb2.Item(id=item_id)
        response = self.stub.DeleteItem(
            marketplace_pb2.ItemManagement(uuid=self.uuid, item=item)
        )
        print(response.message)

    def display_seller_items(self):
        response = self.stub.DisplaySellerItems(
            marketplace_pb2.SellerRegistration(uuid=self.uuid, notificationPort=self.notificationPort)
        )
        for item in response:
            rating = "Unrated" if item.rating == -1 else f"{item.rating} / 5"
            print(f"-----\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {marketplace_pb2.Category.Name(item.category)},\n"
                f"Description: {item.description}.\n"
                f"Quantity Remaining: {item.quantity}\n"
                f"Seller: {item.seller_address}\n"
                f"Rating: {rating}\n"
                f"-----\n")
            
# Define the Notification Service class as per the new proto definition
class NotificationService(marketplace_pb2_grpc.NotificationServiceServicer):
    def NotifyClient(self, request, context):
        print("\n")
        print("=====" * 8)  # Print separator
        print("NOTIFICATION RECEIVED:\n", request.message)
        print("=====" * 8)  # Print separator
        print("\n")
        return marketplace_pb2.Response(message="Acknowledged")

server = None  # Declare server as a global variable

def start_notification_server(port):
    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    marketplace_pb2_grpc.add_NotificationServiceServicer_to_server(NotificationService(), server)
    server.add_insecure_port('0.0.0.0:' + str(port))
    server.start()
    print(f"Notification server listening on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught.")


if __name__ == "__main__":
    port = int(input("Enter the port for the notification server: "))
    notification_thread = threading.Thread(target=start_notification_server, args=(port,), daemon=True).start()
    time.sleep(0.01)  # Add a delay here
    seller = SellerClient('10.190.0.2:50051', port)
    
    while True:
        try:
            print("\n=== Seller Menu ===")
            print("1. Register as Seller")
            print("2. Sell Item")
            print("3. Update Item")
            print("4. Delete Item")
            print("5. Display Seller Items")
            print("6. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                seller.register_seller()
            elif choice == '2':
                name = input("Enter item name: ")
                print("Choose category:\n1. ELECTRONICS\n2. FASHION\n3. OTHERS")
                category_choice = input("Enter choice: ")
                category = marketplace_pb2.ELECTRONICS if category_choice == '1' else marketplace_pb2.FASHION if category_choice == '2' else marketplace_pb2.OTHERS
                quantity = int(input("Enter quantity: "))
                description = input("Enter description: ")
                price = float(input("Enter price: "))
                seller.sell_item(name, category, quantity, description, price)
            elif choice == '3':
                item_id = int(input("Enter item ID to update: "))
                new_quantity = int(input("Enter new quantity: "))
                new_price = float(input("Enter new price: "))
                seller.update_item(item_id, new_quantity, new_price)
            elif choice == '4':
                item_id = int(input("Enter item ID to delete: "))
                seller.delete_item(item_id)
            elif choice == '5':
                seller.display_seller_items()
            elif choice == '6':
                print("Exiting...")
                print("Shutting down the server gracefully...")
                server.stop(0)  # Gracefully stop the server
                print("Server stopped.")
                os._exit(0)  # Forcefully stop the Python interpreter
            else:
                print("Invalid choice. Please choose again.")
        except KeyboardInterrupt:
            print("Exiting...")
            print("Shutting down the server gracefully...")
            server.stop(0)
            print("Server stopped.")
            os._exit(0)