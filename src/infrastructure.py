import csv


def read_orders(data_file):
    """Function which reads a csv with the orders (example is dataClient.csv)
    and converts the data into an array of Orders (the order id is the same as the index of the array);
    each order contains Picks, which are populated with the data.

    Args:
        data_file (string): name of the csv file.

    Returns:
        orders: dict of order objects.

    Example:
    >>> orders = read_data_global("dataClient.csv")
    >>> len(orders) #get the number of all orders
    44640
    >>> orders["044639"].numPicks() #get the number of picks for order with id=44639
    3
    >>> orders["000001"].picks[6]._id # get the id of the 7th pick of order id=00001
    >>> '000016'
    """
    
    #open the file
    with open(data_file, 'r') as datafile:
        reader = csv.reader(datafile, delimiter=';')
        column_names = []
        orders = {}
        current_order_id = "000001"
        previous_order_id = 0
        current_order = Order(current_order_id)
        rownum = 0
        #iterate through each element in the csv and avoid the headers
        for row in reader:
            colnum = 0
            current_pick_data = []
            for col in row:
                if rownum == 0:
                    #populating the header array
                    column_names = column_names + [col]
                else:
                    if colnum == 0:
                        #checking if the order id is the same; if not we create
                        #a new object Order and append it to the orders array
                        if col != current_order_id:
                            orders[previous_order_id] = current_order
                            current_order_id = col
                            current_order = Order(col)
                            current_pick_data = current_pick_data + [col]
                        else:
                            current_pick_data = current_pick_data + [col]
                            previous_order_id = current_order_id
                    else:
                        current_pick_data = current_pick_data + [col]                        
                colnum += 1
            if (rownum > 0):
                #populate the pick object with the obtained data
                pick = Pick(current_pick_data)
                current_order.picks = current_order.picks + [pick]
            rownum += 1
        #add the last order to the array
        orders[current_order_id] = current_order
    return orders


class Order:
    def __init__(self, order_id):
        self.picks = []
        self._order_id = order_id

    #helper function
    def numPicks(self):
        return len(self.picks)


class Batch:
    def __init__(self):
        self.picks = []


class Warehouse:
    #initialize the matrix which will be populated with the distances from csv
    def __init__(self):
        self.dist = {}
    
    def read_distances(self, data_file):
        """Function which reads the csv of the distances between the nodes and
           returns a dictionary of dictionaries with keys of the node id

           Args:
               data_file (string): name of the csv file.
           
           Returns:
               self.dist: distances between the nodes.

           Example:

           >>> warehouse = Warehouse() #initialize warehouse object
           >>> warehouse.read_distances("test.csv") #read the distances
           >>> warehouse.dist["a"] #print all the distances from node "a"
           {'b': '23', 'c': '4', 'a': '5'}
           >>> warehouse.dist["a"]["b"] #get the distance between node "a" and "b"
           '23'

        """
        #open the file
        with open(data_file, 'r') as datafile:
            reader = csv.reader(datafile, delimiter=';')
            array_nodes = []
            rownum = 0
            #iterate through each element in the csv and avoid the headers
            for row in reader:
                colnum = 0
                current_dictionary = {}
                current_node = ""
                for col in row:
                    if rownum == 0:
                        array_nodes = array_nodes + [col]
                    else:
                        if colnum == 0:
                            current_node = col
                        else:
                            current_dictionary[array_nodes[colnum]] = int(col)
                    colnum += 1
                self.dist[current_node] = current_dictionary
                rownum += 1
        return self.dist


class Pick:
    def __init__(self, data_row):
        self._order = data_row[0]
        self._date = data_row[1]
        self._warehouse_location = data_row[2]
        self._start_on = data_row[3]
        self._start_at = data_row[4]
        self._end_on = data_row[5]
        self._end_order_at = data_row[6]
        self._end_pos_at = data_row[7]
        self._batch = data_row[8]
        self._row = data_row[9]
        self._vehicle_nr = data_row[10]
        self._id = data_row[11]
        self._box_nr = data_row[12]
        self._created_on = data_row[13]
        self._created_at = data_row[14]
