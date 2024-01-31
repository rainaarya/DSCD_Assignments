import grpc
import marketplace_pb2
import marketplace_pb2_grpc
import uuid
import threading

class SellerClient:
    def __init__(self, address):
        self.channel = grpc.insecure_channel(address)
        self.stub = marketplace_pb2_grpc.MarketplaceServiceStub(self.channel)
        self.uuid = str(uuid.uuid1())
        self.address = address.split(':')[0]

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
        for notification in self.stub.NotifyClient(marketplace_pb2.Notification()):
            print("NOTIFICATION RECEIVED:\n", notification.message)


if __name__ == "__main__":
    seller = SellerClient('localhost:50051')
    # Start listening for notifications in a separate thread
    threading.Thread(target=seller.listen_for_notifications).start()

    seller.register_seller()
    seller.sell_item("Laptop", marketplace_pb2.ELECTRONICS, 10, "Latest model", 1200.0)
    seller.sell_item("Mobile", marketplace_pb2.ELECTRONICS, 20, "Latest model", 800.0)
    seller.display_seller_items()
    # Add other operations as needed
