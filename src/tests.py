from infrastructure import read_orders, Batch, Order, Pick, Warehouse, get_model_solution, to_csv
from model import Model

from datetime import datetime

ORDERS_FILE = "../data/DatenClient1_day_1.csv"
DIST_FILE = "../data/DistanceMatrix_Final.csv"

NUM_PICKS = 3
MAX_N_BATCHES = 2


def test():
    """A global function which runs all the tests available.

       Args:
       
       Returns:
       
    """
    test_tsp()
    #test_more_batches()
    return ""

def test_more_batches():

    """A global function which forces the model to use several batches. The function iterates once through num of batches and the
       to the number of pick (always iteratively).

           Args: 
           Returns: 
    """
    NUM_PICKS = 5
    MAX_N_BATCHES = 2

    error = ""
    already_created_file = False
    
    current_solution = 1
    num_batches = 1

    iteration_index = 1

    while num_batches == 1:
    
        dist = Warehouse().read_distances(DIST_FILE)

        orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)

        sum_items = 0
        for order_id, order in orders.items():
            sum_items += order.num_picks()

        start = datetime.now()

        model = Model(dist, orders, max_n_batches=MAX_N_BATCHES)

        model.gurobi_model.optimize()

        current_solution = get_model_solution(model, dist)

        num_batches = len(current_solution)

        end = datetime.now()

        iteration_index += 1

        if (iteration_index % 2 == 0):
            NUM_PICKS = NUM_PICKS + 1
        else:
            MAX_N_BATCHES = MAX_N_BATCHES + 1

        to_csv("more_batches_test.csv", current_solution, model, error, already_created_file)

        already_created_file = True

def test_tsp():

    """A global function which iterates through the data and increases the number of nodes in the model by one. The tests
       checks if the solution has n-1 nodes, starts at initial node and ends at the end node. 

           Args: 
           Returns: 
    """
    MAX_N_BATCHES = 1
    NUM_PICKS = 1

    max_num_picks = 8
    

    error = ""
    already_created_file = False

    while NUM_PICKS < max_num_picks:
        dist = Warehouse().read_distances(DIST_FILE)

        orders = read_orders(ORDERS_FILE, num_picks=NUM_PICKS)

        sum_items = 0
        for order_id, order in orders.items():
            sum_items += order.num_picks()


        start = datetime.now()

        model = Model(dist, orders, max_n_batches=MAX_N_BATCHES)

        model.gurobi_model.optimize()

        solution = get_model_solution(model, dist)

        end = datetime.now()

        if len(solution[0].route)-1 > NUM_PICKS + 2:
            error = "The number of edges is " + str(len(solution[0].route - 1)) + "and is exceeding the number of picks (" + str(NUM_PICKS + 2) + ") i.e. a circle is being made in the graph."

        if solution[0].route[0] != "F-20-27":
            if error == "":
                error = "The route is not starting at the starting node"
            else:
                error = error + ", " + "The route is not starting at the starting node"

        if solution[0].route[len(solution[0].route)-1] != "F-20-28":
            if error == "":
                error = "The route is not ending at the end node."
            else:
                error = error + ", " + "The route is not ending at the end node."

        if ["F-20-27", "F-20-28"] not in solution[0].edges or ["F-20-28", "F-20-27"] not in solution[0].edges:
            if error == "":
                error = "The route does not include the edge between the starting and end node."
            else:
                error = error + ", " + "The route does not include the edge between the starting and end node."

        to_csv("one_batch_test.csv", solution, model, error, already_created_file)

        NUM_PICKS = NUM_PICKS + 1
        already_created_file = True
        error = ""


if __name__ == '__main__':
    test()
