import csv
import gurobipy as gp

def to_csv(file_name, solution, model, error_message, already_created):
    
    """A global function which writes the results into a csv file. It needs
       the file name where to write and more importantly the model and solution
       objects. The output is a csv file.

    Args: file_name (string): the name of the file
          solution (list of batches): list of batches which is an output of read_solution function
          model (Model): the model used to obtain the optimal solution
          error_message (string): it throws the error messages which were collected during testing
          already_created (bool): it indicates whether the csv file was already created or not
          
    Returns: csv file in the same folder as the infrastructure.py
    
    """

    fieldnames = ['number of items', 'route', 'edges', 'distances', 'total distance', 'Error']
    if not already_created:
        with open(file_name, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for batch in solution:
                route_length = len(batch.route)
                distances_length = len(batch.distances)
                writer.writerow({'number of items': route_length, 'route': batch.route, 'edges': batch.edges,
                                 'distances': batch.distances,'total distance': batch.total_distance,
                                 'Error': error_message})
            writer.writerow({'number of items': "----", 'route': "-----", 'edges': "----",
                             'distances': "----", 'total distance': "----", 'Error': "----"})
    else:
        with open(file_name, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            for batch in solution:
                route_length = len(batch.route)
                distances_length = len(batch.distances)
                writer.writerow({'number of items': route_length, 'route': batch.route, 'edges': batch.edges,
                                 'distances': batch.distances, 'total distance': batch.total_distance,
                                 'Error': error_message})

            writer.writerow({'number of items': "----", 'route': "-----", 'edges': "----",
                             'distances': "----", 'total distance': "----", 'Error': "----"})

                    
def get_model_solution(model, dist):
    
    """A global function which reads the solution of the model. It should
       be used in order to obtain all the relevant data of the solution
       
    Args: model (Model): the model used to obtain the optimal solution
          dist (dictionary): the distance matrix from Warehouse.dist
          
    Returns: A list of Batch objects
    
    """
    
    batches = []
    curr_batch = -1
    index = -1
    for batch in range(model._constants['max_n_batches']):
        index_i = 0
        for node_i in model._nodes:
            for node_j in model._nodes[(index_i +1):]:
                a_var_reference = model.gurobi_model.getVarByName('x' + '^' + str(batch) + '_' + node_i + '_' + node_j)

                #if x_k_i_j = 1 and if the current batch does not belong to the saved one then create a new Batch in the list
                #and save the route and distance
                if a_var_reference.X > 0.5 and batch != curr_batch:
                    batches.append(Batch())
                    curr_batch = batch
                    index += 1
                    batches[index].read_route(node_i, node_j, dist)
                #if the batch is not new then just store the route and distance in the current batch
                elif a_var_reference.X > 0.5:
                    batches[index].read_route(node_i, node_j, dist)
            index_i += 1
        if (index > -1):
            batches[index].complete_route(dist)
            batches[index].find_edges()
    return batches


def read_orders(data_file, num_picks=None):
    
    """Function which reads a csv with the orders (example is dataClient.csv)
    and converts the data into an array of Orders (the order id is the same as the index of the array);
    each order contains Picks, which are populated with the data.
    
    Args:
                 data_file (string): name of the csv file.
        num_picks (float, optional): max overall total number of items, ie picks, that should be read 
                                     from the csv file.
                                     
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
            if (num_picks != None and rownum > num_picks):
                break
        #add the last order to the array
        orders[current_order_id] = current_order
    return orders

class Order:
    def __init__(self, order_id):
        self.picks = []
        self._order_id = order_id

    #helper function
    def num_picks(self):
        return len(self.picks)


class Batch:
    def __init__(self):
        self.route = []
        self.distances = []
        self.edges = []
        self.rest_of_circle = {}
        self.total_distance = 0

    def read_route(self, node_i, node_j, dist):
        
        """A member function of the class Batch, which takes two nodes as insput
           and populates the route vector with the nodes by adding node_i or node_j
           (depends on which node is already there) to the route vector.

           If none of the nodes is in the vector then you populate the nodes into
           the self.rest_of_circle dictionary. That can happen, because the variables
           do not have to be populated as a circle.

           Args: node_i (pick._warehouse_location): the first node of the route
                 node_j (pick._warehouse_location): the second node of the route
                 dist (distance matrix): the distance matrix populated in a csv
                 
           Returns:

           Example: Lets say that we have following nodes (2,3), (3,4), (1,2)
           then by going iteratively through the nodes we have:

           route = [1, 2, 3]
           
        """

        if node_j == "F-20-27" or node_i == "F-20-28":
            node_temp = node_i
            node_i = node_j
            node_j = node_temp

        distance = dist[node_i][node_j]

        if self.route == []:
            self.route.append(node_i)
            self.route.append(node_j)

            self.distances.append(distance)

            self.total_distance = self.total_distance + distance
        elif node_i in self.route:
            if self.route[0] == node_i:
                self.route.insert(0, node_j)

                self.distances.insert(0, distance)

                self.total_distance = self.total_distance + distance
            elif self.route[len(self.route)-1] == node_i:
                self.route.append(node_j)

                self.distances.append(distance)

                self.total_distance = self.total_distance + distance
        elif node_j in self.route:
            if self.route[0] == node_j:
                self.route.insert(0, node_i)

                self.distances.append(distance)

                self.total_distance = self.total_distance + distance
            elif self.route[len(self.route)-1] == node_j:
                self.route.append(node_i)

                self.distances.append(distance)

                self.total_distance = self.total_distance + distance
        else:
            self.rest_of_circle[node_i] = node_j

    def complete_route(self, dist):
        
        """A member function of the class Batch, which completes the circle that the
           read_route cannot. This is a gaps function which takes the nodes in self.rest_of_circle
           which could not be populated in self.route with the read_route function.

           Args: dist (distance matrix): the distance matrix populated in a csv
           
           Returns:

           Example: Lets say that we have following nodes (1,2), (2,3), (4,5), (3,4)
           then by going iteratively through the nodes we have:

           route = [1, 2, 3]

           and (4,5) cannot be applied to route. Therefore we store it in self.rest_of_circle

           i.e. rest_of_circle = {4: 5}

           and then we move on with the 4th node which can be applied to route i.e.

           route = [1, 2, 3, 4]

           Now complete_route function comes into play. It uses all the nodes stored in
           rest_of_circle and tries to add them to the existing route by using read_route.

           i.e. route = [1, 2, 3, 4, 5]
           
        """


        max_iter = 5

        initial_length = len(self.route)
        if self.rest_of_circle == {}:
            return ""
        else:
            i = 0
            while len(self.route) < initial_length + len(self.rest_of_circle) and i < max_iter:
                for node_i, node_j in self.rest_of_circle.items():
                    if node_i not in self.route or node_j not in self.route:
                        self.read_route(node_i, node_j, dist)
                i += 1

    def find_edges(self):

        """

           Member function which reads all the edges out of a route
           
           Args:
               
           
           Returns:
               self.edges: A list of lists of two elements which indicates the edge.


        """
        index = 1
        while index < len(self.route):
            self.edges.append([self.route[index-1], self.route[index]])
            index += 1
            
            

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
