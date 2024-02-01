import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import uuid
import threading
import time

class SellerClient:
    def __init__(self, server_address, buyer_address):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.uuid = str(uuid.uuid1())
        self.address = buyer_address

    def register_seller(self):
        response = self.stub.RegisterSeller(
            marketplace_pb2.SellerRegistration(address=self.address, uuid=self.uuid)
        )
        print(response.message)

    def sell_item(self, name, category, quantity, description, price):
        item = marketplace_pb2.Item(
            name=name, 
            category=category, 
            quantity=quantity, 
            description=description, 
            price=price, 
            seller_address=self.address
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
            marketplace_pb2.SellerRegistration(address=self.address, uuid=self.uuid)
        )
        for item in response:
            print(item)
    
    def listen_for_notifications(self):
        try:
            for notification in self.stub.NotifyClient(marketplace_pb2.Address(address=self.address)):
                print("NOTIFICATION RECEIVED:\n", notification.message)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    seller = SellerClient('localhost:50051', 'seller_ip:seller_port')
    notification_thread = threading.Thread(target=seller.listen_for_notifications)
    notification_thread.daemon = True  # Set the thread as a daemon
    notification_thread.start()

    seller.register_seller()
    seller.sell_item("Laptop", marketplace_pb2.ELECTRONICS, 10, "Latest model", 1200.0)
    seller.sell_item("Mobile", marketplace_pb2.ELECTRONICS, 20, "Latest model", 800.0)
    seller.display_seller_items()
    # Add other operations as needed

    try:
        while True:
            # Keep the main thread running.
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated by user")
        # Here you can add any cleanup code if necessary before exiting.
        # The daemon thread will be terminated when the main program exits.
