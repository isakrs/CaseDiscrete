from infrastructure import read_orders, Batch, Order, Pick, Warehouse
from test_model import *


ORDERS_FILE = "../data/DatenClient1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"


def main():
    dist = Warehouse().read_distances(DIST_FILE)
    print("Size of the dist: ", len(dist))

    orders = read_orders(ORDERS_FILE)
    print("Number of orders: ", len(orders))

if __name__ == '__main__':
    main()
