from infrastructure import read_orders, Batch, Order, Pick, Warehouse
from model import Model

from datetime import datetime


ORDERS_FILE = "../data/DatenClient1_day_1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"

NUM_PICKS = 88 # first 100 orders is 438 picks
VOL = 6


def main():
    dist = Warehouse().read_distances(DIST_FILE)

    orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)
    print("Number of orders: ", len(orders))

    start = datetime.now()
    print('Model start time: ', str(start))

    model = Model(dist, orders, volume=VOL)

    model.optimize()

    end = datetime.now()
    print('Model duration time: ', str(end - start), '\nModel ended: ', str(end))

    model.solution_batches()

    print('number of used nodes: ', len(model._nodes))
    print('number of variables: ', len(model._vars))
    print('number of constants: ', len(model._constants))

if __name__ == '__main__':
    main()
