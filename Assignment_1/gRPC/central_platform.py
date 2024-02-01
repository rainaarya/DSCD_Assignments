import grpc
from concurrent import futures
import marketplace_pb2
import marketplace_pb2_grpc
import queue
import os

class MarketplaceService(marketplace_pb2_grpc.MarketplaceServiceServicer):
    def __init__(self):
        # Initialize data structures for storing information
        self.sellers = {}  # Stores seller details
        self.items = {}  # Stores item details
        self.item_id_counter = 1  # Unique item ID generator
        self.wishlists = {}  # Stores buyer wishlists
        self.notifications = {}  # key: client address, value: queue of notifications

    def RegisterSeller(self, request, context):
        # Register a new seller
        if request.address in self.sellers:
            return marketplace_pb2.Response(message="FAIL")
        self.sellers[request.address] = request.uuid
        print(f"\nSeller join request from {request.address}, uuid = {request.uuid}")
        return marketplace_pb2.Response(message="SUCCESS")

    def SellItem(self, request, context):
        # Add a new item to the marketplace
        item = request.item
        item.id = self.item_id_counter
        self.items[self.item_id_counter] = item
        self.item_id_counter += 1
        print(f"\nSell Item request from {request.uuid}")
        return marketplace_pb2.Response(message=f"SUCCESS, Item ID: {item.id}")

    def UpdateItem(self, request, context):
        if request.uuid not in self.sellers.values():
            return marketplace_pb2.Response(message="FAIL: Unrecognized Seller UUID")
        if request.item.id not in self.items:
            return marketplace_pb2.Response(message="FAIL: Item ID not found")

        item = self.items[request.item.id]
        item.quantity = request.item.quantity
        item.price = request.item.price
        # Other fields like name, description, etc., can also be updated if needed

        # Notify all buyers who have wish-listed this item
        notification_message = f"The Following Item has been updated:\n\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {marketplace_pb2.Category.Name(item.category)}\nDescription: {item.description}.\nQuantity Remaining: {item.quantity}\nRating: {item.rating}/5 | Seller: {item.seller_address}\n"
        for buyer_address, wishlist in self.wishlists.items():  # Iterate through all wishlists
            if item.id in wishlist:  # Check if the item is in the current wishlist
                if buyer_address in self.notifications:  # Check if the buyer is subscribed to notifications
                    notification = marketplace_pb2.Notification(item=item, message=notification_message)
                    self.notifications[buyer_address].put(notification)  # Add notification to the buyer's queue

        print(f"\nUpdate Item {item.id} request from {request.uuid}")
        return marketplace_pb2.Response(message="SUCCESS")

    def DeleteItem(self, request, context):
        if request.uuid not in self.sellers.values():
            return marketplace_pb2.Response(message="FAIL: Unrecognized Seller UUID")
        if request.item.id not in self.items:
            return marketplace_pb2.Response(message="FAIL: Item ID not found")

        del self.items[request.item.id]
        print(f"\nDelete Item {request.item.id} request from {request.uuid}")
        return marketplace_pb2.Response(message="SUCCESS")

    def DisplaySellerItems(self, request, context):
        if request.uuid not in self.sellers.values():
            return  # Stream closure

        for item_id, item in self.items.items():
            if item.seller_address == request.address:
                yield item
        print(f"\nDisplay Items request from {request.address}")
    
    # buyer stuff
    def SearchItem(self, request, context):
        category_enum = marketplace_pb2.Category.Name(request.category)
        for item_id, item in self.items.items():
            if (request.category == marketplace_pb2.Category.Value('ANY') or item.category == request.category) and \
            (request.item_name == "" or request.item_name.lower() in item.name.lower()):
                yield item
        print(f"\nSearch request for Item name: {request.item_name}, Category: {category_enum}")


    def BuyItem(self, request, context):
        if request.item_id not in self.items:
            return marketplace_pb2.Response(message="FAIL: Item ID not found")
        
        item = self.items[request.item_id]
        if item.quantity < request.quantity:
            return marketplace_pb2.Response(message="FAIL: Not enough stock")
        
        item.quantity -= request.quantity
        # Trigger notification to the seller
        seller_notification = marketplace_pb2.Notification(
            item=item,
            message=f"Item {item.id} purchased by {request.buyer_address}"
        )
        seller_address = item.seller_address
        if seller_address in self.notifications:
            self.notifications[seller_address].put(seller_notification)

        print(f"\nBuy request {request.quantity} of item {request.item_id}, from {request.buyer_address}")
        return marketplace_pb2.Response(message="SUCCESS")
    
    def AddToWishList(self, request, context):
        if request.item_id not in self.items:
            return marketplace_pb2.Response(message="FAIL: Item ID not found")

        if request.buyer_address not in self.wishlists:
            self.wishlists[request.buyer_address] = set()

        self.wishlists[request.buyer_address].add(request.item_id)
        print(f"\nWishlist request of item {request.item_id}, from {request.buyer_address}")
        return marketplace_pb2.Response(message="SUCCESS")

    def RateItem(self, request, context):
        if request.item_id not in self.items:
            return marketplace_pb2.Response(message="FAIL: Item ID not found")
        
        item = self.items[request.item_id]
        if not hasattr(item, 'total_rating'):
            item.total_rating = 0
            item.num_ratings = 0

        item.total_rating += request.rating
        item.num_ratings += 1
        item.rating = item.total_rating / item.num_ratings
        print(f"\n{request.buyer_address} rated item {request.item_id} with {request.rating} stars.")
        return marketplace_pb2.Response(message="SUCCESS")
    
    def NotifyClient(self, request, context):
        client_address = request.address
        #print(f"Client {client_address} connected to meeeee!!")
        self.notifications[client_address] = queue.Queue()

        try:
            while True:
                while not self.notifications[client_address].empty():
                    notification = self.notifications[client_address].get()
                    yield notification
        except grpc.RpcError as e:
            del self.notifications[client_address]


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    marketplace_pb2_grpc.add_MarketplaceServiceServicer_to_server(MarketplaceService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started. Listening on '[::]:50051'")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught. Shutting down the server gracefully...")
        server.stop(0)  # Gracefully stop the server
        print("Server stopped.")
        os._exit(0)  # Forcefully stop the Python interpreter


if __name__ == '__main__':
    serve()
