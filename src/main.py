from infrastructure import read_orders, Batch, Order, Pick, Warehouse
from model import Model

from datetime import datetime


ORDERS_FILE = "../data/DatenClient1_day_1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"


def main():
    dist = Warehouse().read_distances(DIST_FILE)
    print("Size of the dist: ", len(dist))

    orders = read_orders(ORDERS_FILE)
    print("Number of orders: ", len(orders))

    start = datetime.now()
    print('Model start time: ', str(start))

    model = Model(dist, orders)

    model.gurobi_model.optimize()

    end = datetime.now()
    print('Model duration time: ', str(end - start), '\nModel ended: ', str(end))

    print('number of used nodes: ', len(model._nodes))
    print('number of variables: ', len(model._vars))
    print('number of constants: ', len(model._constants))

if __name__ == '__main__':
    main()
