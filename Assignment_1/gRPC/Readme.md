
---

# 🛍️ Online Shopping Platform - gRPC Implementation 🛒

## 🌐 Overview

This project implements an Online Shopping Platform using gRPC, allowing communication between a central marketplace, sellers, and buyers. The platform is designed to demonstrate the practical application of gRPC in a distributed system where different components interact over a network. It uses Protocol Buffers for efficient data serialization.

### 🧩 Components

- **🏪 Market (Central Platform):** Central node for handling all operations related to item listings, seller and buyer registrations, and notifications.
- **👩‍💼 Seller (Client):** Clients that interact with the Market to manage their items (add, update, delete) and receive notifications about item purchases.
- **👨‍💼 Buyer (Client):** Clients that search for, buy items, add items to a wishlist, and rate items. Buyers also receive notifications when wish-listed items are updated.

## 📚 Dependencies

- Python 3.x 🐍
- gRPC and gRPC tools 🛠️
- Protocol Buffers (proto3) 📦

## 💻 Installation

Before running the application, ensure you have Python and pip installed. Then, install the required Python packages:

```bash
pip install grpcio grpcio-tools
```

## 📁 Files Description

- `marketplace.proto`: Contains Protocol Buffers message definitions and the service API for the marketplace.
- `central_platform.py`: Implements the server side of the marketplace service.
- `seller.py`: Client script for seller operations.
- `buyer.py`: Client script for buyer operations.

## 📝 `marketplace.proto` Overview

This file defines the structure of data and services used across the platform, facilitating communication between the marketplace server and the clients (sellers and buyers).

- **Enum `Category`:** Defines categories for items (ELECTRONICS, FASHION, OTHERS, ANY) to help in filtering search results.
- **Message `Item`:** Represents an item with fields for ID, name, category, description, quantity, price, rating, and seller address.
- **Message `SellerRegistration`:** Used for registering a seller with the marketplace, containing a UUID and notification port.
- **Message `ItemManagement`:** For adding, updating, and deleting items, including a UUID for seller identification and an `Item` message.
- **Message `BuyerOperation`:** Supports buyer operations like searching, buying, wishlisting, and rating items, with fields for item ID, quantity, category, rating, item name, and notification port.
- **Message `Response`:** A generic response message containing a result message (e.g., SUCCESS, FAIL).
- **Message `Notification`:** For sending notifications with an `Item` message and a custom message.
- **Service `MarketplaceService` and `NotificationService`:** Define RPC methods for the marketplace operations and notification delivery, respectively.

## 📚 `central_platform.py` Functions

This script implements the server-side logic of the marketplace, handling requests from both sellers and buyers.

- **Class `MarketplaceService`:** Implements the marketplace service defined in the `marketplace.proto`.
    - **`RegisterSeller`:** Registers a new seller with their UUID and notification port.
    - **`SellItem`:** Allows sellers to list a new item for sale.
    - **`UpdateItem`:** Sellers can update details of their listed items.
    - **`DeleteItem`:** Sellers can remove their listed items from the marketplace.
    - **`DisplaySellerItems`:** Lists all items a seller has put up for sale.
    - **`SearchItem`:** Allows buyers to search for items by name and/or category.
    - **`BuyItem`:** Buyers can purchase items, which also updates the item's quantity.
    - **`AddToWishList`:** Buyers can add items to a wishlist to receive updates.
    - **`RateItem`:** Buyers can rate items.
- **`send_notification`:** A utility function to send notifications to clients using their notification service.

## 📚 `seller.py` Functions

This script represents the seller client, allowing interaction with the marketplace for item management and receiving notifications.

- **Class `SellerClient`:** Encapsulates seller operations.
    - **`register_seller`:** Registers the seller with the marketplace.
    - **`sell_item`:** Lists a new item for sale.
    - **`update_item`:** Updates details of a listed item.
    - **`delete_item`:** Removes an item from the marketplace.
    - **`display_seller_items`:** Displays all items listed by the seller.
- **Class `NotificationService`:** Handles incoming notifications for the seller.
- **`start_notification_server`:** Starts a gRPC server to listen for notifications.

## 📚 `buyer.py` Functions

This script represents the buyer client, enabling searching, buying, wishlisting, and rating items, along with receiving notifications.

- **Class `BuyerClient`:** Encapsulates buyer operations.
    - **`search_item`:** Searches for items based on name and/or category.
    - **`buy_item`:** Purchases an item.
    - **`add_to_wishlist`:** Adds an item to the wishlist.
    - **`rate_item`:** Rates an item.
- **Class `NotificationService`:** Handles incoming notifications for the buyer.
- **`start_notification_server`:** Starts a gRPC server to listen for notifications.

## 📣 Notification Service

Both seller and buyer scripts include a simple notification service, running on a separate thread, to display real-time updates and notifications related to item transactions and updates.

## 🚀 Running the Application

1. **Compile the `.proto` file into Python files** 📝

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. marketplace.proto
```

This will generate `marketplace_pb2.py` and `marketplace_pb2_grpc.py` files that are required for the server and client scripts.

2. **Start the Central Platform:** 🏪

```bash
python central_platform.py
```

3. **Start a Seller Client:** 👩‍💼

Open a new terminal window and run:

```bash
python seller.py
```

Follow the prompts to perform seller operations.

4. **Start a Buyer Client:** 👨‍💼

Open another terminal window and run:

```bash
python buyer.py
```

Follow the prompts to perform buyer operations.

---

**Note:** 📝 Replace any placeholder paths, IP addresses, or ports with actual values used in your environment. This readme assumes that the `central_platform.py`, `seller.py`, and `buyer.py` scripts are located in the same directory and are run from the command line.