import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import threading

class BuyerClient:
    def __init__(self, address):
        self.channel = grpc.insecure_channel(address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.address = address.split(':')[0]

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
            for notification in self.stub.NotifyClient(marketplace_pb2.Empty()):
                print("NOTIFICATION RECEIVED:\n", notification.message)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")



if __name__ == "__main__":
    buyer = BuyerClient('localhost:50051')
    # Start listening for notifications in a separate thread
    threading.Thread(target=buyer.listen_for_notifications).start()
    
    buyer.search_item("", marketplace_pb2.ANY)
    buyer.buy_item(1, 2)
    # Add other operations as needed
