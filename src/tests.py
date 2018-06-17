from infrastructure import read_orders, Batch, Order, Pick, Warehouse, read_solution
from model import Model

from datetime import datetime

ORDERS_FILE = "../data/DatenClient1_day_1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"

NUM_PICKS = 10
MAX_N_BATCHES = 2

def test():
    test_tsp()
    test_more_batches()
    return ""

def test_more_batches():
    NUM_PICKS = 10
    MAX_N_BATCHES = 2
    
    current_solution = 1
    num_batches = 1

    iteration_index = 1

    while num_batches == 1:
    
        dist = Warehouse().read_distances(DIST_FILE)
        print("Size of the dist: ", len(dist))

        orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)
        print("Number of orders: ", len(orders))

        sum_items = 0
        for order_id, order in orders.items():
            sum_items += order.num_picks()
        print("Number of items: ", sum_items)

        start = datetime.now()
        print('Model start time: ', str(start))

        model = Model(dist, orders, max_n_batches=MAX_N_BATCHES)

        model.gurobi_model.optimize()

        current_solution = read_solution(model, dist)

        num_batches = len(current_solution)

        end = datetime.now()
        print('Model duration time: ', str(end - start), '\nModel ended: ', str(end))

        print('number of used nodes: ', len(model._nodes))
        print('number of variables: ', len(model._vars))
        print('number of constants: ', len(model._constants))

        iteration_index += 1

        if (iteration_index % 2 == 0):
            NUM_PICKS = NUM_PICKS + 1
        else:
            MAX_N_BATCHES = MAX_N_BATCHES + 1
        
    return ""

def test_tsp():
    MAX_N_BATCHES = 1
    print(MAX_N_BATCHES)
    print(NUM_PICKS)
    
    dist = Warehouse().read_distances(DIST_FILE)
    print("Size of the dist: ", len(dist))

    orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)
    print("Number of orders: ", len(orders))

    sum_items = 0
    for order_id, order in orders.items():
        sum_items += order.num_picks()
    print("Number of items: ", sum_items)

    start = datetime.now()
    print('Model start time: ', str(start))

    model = Model(dist, orders, max_n_batches=MAX_N_BATCHES)

    model.gurobi_model.optimize()

    read_solution(model, dist)

    end = datetime.now()
    print('Model duration time: ', str(end - start), '\nModel ended: ', str(end))

    print('number of used nodes: ', len(model._nodes))
    print('number of variables: ', len(model._vars))
    print('number of constants: ', len(model._constants))

if __name__ == '__main__':
    test()
