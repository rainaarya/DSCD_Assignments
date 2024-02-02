import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import uuid
import threading

class SellerClient:
    def __init__(self, server_address):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.uuid = str(uuid.uuid1())
        #self.address = buyer_address

    def register_seller(self):
        response = self.stub.RegisterSeller(
            marketplace_pb2.SellerRegistration(uuid=self.uuid)
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
            marketplace_pb2.SellerRegistration(uuid=self.uuid)
        )
        for item in response:
            rating = "Unrated" if item.rating == -1 else f"{item.rating} / 5"
            print(f"-----\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {marketplace_pb2.Category.Name(item.category)},\n"
                f"Description: {item.description}.\n"
                f"Quantity Remaining: {item.quantity}\n"
                f"Seller: {item.seller_address}\n"
                f"Rating: {rating}\n"
                f"-----\n")
    
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
    seller = SellerClient('127.0.0.1:50051')
    notification_thread = threading.Thread(target=seller.listen_for_notifications)
    notification_thread.daemon = True  # Set the thread as a daemon
    notification_thread.start()

    while True:
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
            break
        else:
            print("Invalid choice. Please choose again.")
