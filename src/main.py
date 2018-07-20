from infrastructure import read_orders, Batch, Order, Pick, Warehouse
from model import Model

from datetime import datetime


ORDERS_FILE = "../data/example.csv"
DIST_FILE = "../data/dist.csv"

NUM_PICKS = [40]
# first 100 orders is 438 picks
VOL = 6         # max number of orders on tray

MIPGAP = 1000   # 1000 means, 1000 mm (1 meter) away from optimial solution


def main():
    dist = Warehouse().read_distances(DIST_FILE)

    file_string = str()

    for n_picks in NUM_PICKS:
        orders = read_orders(ORDERS_FILE, num_picks=n_picks)

        start = datetime.now()
        model = Model(dist, orders, volume=VOL)
        model.optimize()
        end = datetime.now()
        duration = end - start

        model_string = str()
        model_string = "New Model" + '\n'
        model_string += "Number of items: " + str(n_picks) + '\n'
        model_string += "Number of orders: " + str(len(orders)) + '\n'
        model_string += "Number of nodes: " + str(len(model._nodes)) + '\n'
        model_string += "Number of variables: " + str(model.numVars) + '\n'
        model_string += "Number of constraints: " + str(model.numConstrs) + '\n'
        model_string += "Model duration: " + str(duration) + '\n'
        model_string += "Model duration seconds: " + str(duration.seconds) + '\n'
        model_string += "Model batches: \n"
        model_string += model.solution_batches()
        model_string += '\n'
        file_string += model_string
        print(model_string)

    f_name = "results/new_model_100_items_results.txt"
    with open(f_name, 'w') as the_file:
        the_file.write(file_string)

if __name__ == '__main__':
    main()
