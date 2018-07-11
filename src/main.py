from infrastructure import read_orders, Batch, Order, Pick, Warehouse, get_model_solution
from model import Model
from tests import test_tsp

from datetime import datetime


ORDERS_FILE = "../data/DatenClient1_day_1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"

NUM_PICKS = 10
VOLUME = 6


def main():
    dist = Warehouse().read_distances(DIST_FILE)
    orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)
    sum_items = 0
    for order_id, order in orders.items():
        sum_items += order.num_picks()

    start = datetime.now()
    print('Model start time: ', str(start))

    model = Model(dist, orders, volume=VOLUME)
    model.gurobi_model.optimize()

    end = datetime.now()

    print('Model duration time: ', str(end - start), '\n seconds: ', (end - start).seconds, '\nModel ended: ', str(end))
    print("Number of orders: ", len(orders))
    print("Number of items: ", sum_items)

    print('number of used nodes: ', len(model._nodes))
    print('number of variables: ', model.gurobi_model.numVars)
    print('number of constraints: ', model.gurobi_model.numConstrs)

    batches = get_model_solution(model, dist)
    for batch in batches:
        print('batch: \n', batch.__dict__)

    test_tsp()

if __name__ == '__main__':
    main()
