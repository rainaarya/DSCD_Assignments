import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import threading
import time

class BuyerClient:
    def __init__(self, server_address, buyer_address):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.address = buyer_address

    def search_item(self, item_name, category):
        response = self.stub.SearchItem(
            marketplace_pb2.BuyerOperation(buyer_address=self.address, item_name=item_name, category=category)
        )
        for item in response:
            print(item)

    def buy_item(self, item_id, quantity):
        response = self.stub.BuyItem(
            marketplace_pb2.BuyerOperation(item_id=item_id, quantity=quantity, buyer_address=self.address)
        )
        print(response.message)

    def add_to_wishlist(self, item_id):
        response = self.stub.AddToWishList(
            marketplace_pb2.BuyerOperation(item_id=item_id, buyer_address=self.address)
        )
        print(response.message)

    def rate_item(self, item_id, rating):
        response = self.stub.RateItem(
            marketplace_pb2.BuyerOperation(item_id=item_id, rating=rating, buyer_address=self.address)
        )
        print(response.message)
    
    def listen_for_notifications(self):
        try:
            for notification in self.stub.NotifyClient(marketplace_pb2.Address(address=self.address)):
                print("NOTIFICATION RECEIVED:\n", notification.message)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")



if __name__ == "__main__":
    buyer = BuyerClient('localhost:50051', 'buyer_ip:buyer_port')
    notification_thread = threading.Thread(target=buyer.listen_for_notifications)
    notification_thread.daemon = True  # Set the thread as a daemon
    notification_thread.start()
    
    buyer.search_item("", marketplace_pb2.ANY)
    buyer.buy_item(1, 2)
    # Add other operations as needed
    try:
        while True:
            # Keep the main thread running.
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated by user")
        # Here you can add any cleanup code if necessary before exiting.
        # The daemon thread will be terminated when the main program exits.
