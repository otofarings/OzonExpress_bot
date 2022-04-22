import os

from data.config import DEBUG_FOLDER


async def get_orders_from_local():
    orders = []
    for file in os.listdir(DEBUG_FOLDER):
        if file.endswith((".csv", ".txt")):
            with open(f"{DEBUG_FOLDER}/{file}", "r") as new_orders:
                for order in new_orders:
                    orders.append(eval(order))
    return orders


if __name__ == "__main__":
    pass
