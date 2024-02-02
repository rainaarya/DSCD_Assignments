import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import threading
import time

class BuyerClient:
    def __init__(self, server_address):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        #self.address = buyer_address

    def search_item(self, item_name, category):
        response = self.stub.SearchItem(
            marketplace_pb2.BuyerOperation(item_name=item_name, category=category)
        )
        for item in response:
            rating = "Unrated" if item.rating == -1 else f"{item.rating} / 5"
            print(f"-----\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {marketplace_pb2.Category.Name(item.category)},\n"
                f"Description: {item.description}.\n"
                f"Quantity Remaining: {item.quantity}\n"
                f"Seller: {item.seller_address}\n"
                f"Rating: {rating}\n"
                f"-----\n")

    def buy_item(self, item_id, quantity):
        response = self.stub.BuyItem(
            marketplace_pb2.BuyerOperation(item_id=item_id, quantity=quantity)
        )
        print(response.message)

    def add_to_wishlist(self, item_id):
        response = self.stub.AddToWishList(
            marketplace_pb2.BuyerOperation(item_id=item_id)
        )
        print(response.message)

    def rate_item(self, item_id, rating):
        response = self.stub.RateItem(
            marketplace_pb2.BuyerOperation(item_id=item_id, rating=rating)
        )
        print(response.message)
    
    def listen_for_notifications(self):
        try:
            for notification in self.stub.NotifyClient(marketplace_pb2.Empty()):
                print("\n")
                print("=====" * 8)  # Print separator
                print("NOTIFICATION RECEIVED:\n", notification.message)
                print("=====" * 8)  # Print separator
                print("\n")
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")



if __name__ == "__main__":
    buyer = BuyerClient('127.0.0.1:50051')
    notification_thread = threading.Thread(target=buyer.listen_for_notifications)
    notification_thread.daemon = True  # Set the thread as a daemon
    notification_thread.start()

    while True:
        print("\n=== Buyer Menu ===")
        print("1. Search for Item")
        print("2. Buy Item")
        print("3. Add Item to Wishlist")
        print("4. Rate Item")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            item_name = input("Enter item name (leave blank for all items): ")
            print("Choose category:\n1. ELECTRONICS\n2. FASHION\n3. OTHERS\n4. ANY")
            category_choice = input("Enter choice: ")
            category = marketplace_pb2.ELECTRONICS if category_choice == '1' else marketplace_pb2.FASHION if category_choice == '2' else marketplace_pb2.OTHERS if category_choice == '3' else marketplace_pb2.ANY
            buyer.search_item(item_name, category)
        elif choice == '2':
            item_id = int(input("Enter item ID to buy: "))
            quantity = int(input("Enter quantity: "))
            buyer.buy_item(item_id, quantity)
        elif choice == '3':
            item_id = int(input("Enter item ID to add to wishlist: "))
            buyer.add_to_wishlist(item_id)
        elif choice == '4':
            item_id = int(input("Enter item ID to rate: "))
            rating = int(input("Enter rating (1-5): "))
            buyer.rate_item(item_id, rating)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please choose again.")