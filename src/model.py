import gurobipy as gp
import itertools
import math


NAME_START_NODE = "F-20-28"
NAME_END_NODE = "F-20-27"


def _max_order_size(orders):
    """Returns number of items in largest order"""
    max_order_size = 0
    for order in orders:
        if (max_order_size < orders[order].num_picks()):
            max_order_size = orders[order].num_picks()
    return max_order_size

def _subtourelim(model, where):
    """This function adds a subtour constraint to model if one exists."""
    if where == gp.GRB.callback.MIPSOL:
        # for every batch, make a list of used edges
        used_edges = [[] for i in range(model._constants['max_n_batches'])]
        for batch_k in range(model._constants['max_n_batches']):
            batch_k_vars = list()
            for i in range(len(model._nodes)-1):
                for j in range(i+1, len(model._nodes)):                
                    var = model._vars['x', batch_k, model._nodes[i], model._nodes[j]]
                    batch_k_vars.append(var)
            sol_batch_k = model.cbGetSolution(batch_k_vars)
            sol_batch_k_index = 0
            for i in range(len(model._nodes)-1):
                for j in range(i+1, len(model._nodes)):
                    if sol_batch_k[sol_batch_k_index] > 0.5:
                        used_edges[batch_k].append((model._nodes[i], model._nodes[j]))
                    sol_batch_k_index += 1

        # for every batch, make a list of used nodes
        used_nodes = [[] for i in range(model._constants['max_n_batches'])]
        for batch_k in range(model._constants['max_n_batches']):
            for node in model._nodes:
                var = model._vars['B', batch_k, node]
                if model.cbGetSolution(var) > 0.5: # then node is used
                    used_nodes[batch_k].append(node)

            # only nodes where items are picked have been added to used_nodes[batch_k]
            if len(used_nodes[batch_k]) > 0: # if picks in batch_k, then start and end nodes as well
                used_nodes[batch_k].append(NAME_START_NODE)
                used_nodes[batch_k].append(NAME_END_NODE)

        # all necessary info is now attained in order to find subtours
        # time to add constraints to prohibit the subtours
        # this the necessary constraints of constraints 4 in the Technical Documentation.pdf
        for batch_k in range(model._constants['max_n_batches']):
            if len(used_nodes[batch_k]) > 0: # then check/correct the check the cycle
                # function subtour finds the shortest cycle per batch
                tour = _subtour(used_edges[batch_k])
                if tour != None and len(tour) < len(used_nodes[batch_k]): # then a subtour exists
                    # TODO: Should we keep this print. Might be nice to have to see that 
                    # the model is still running.
                    
                    # adding this subtour constraint for every batch
                    # so that the same subtour isn't just created in another batch
                    for batch in range(model._constants['max_n_batches']):
                        expr = 0
                        for node_i, node_j in tour:
                            expr += model._vars['x', batch, node_i, node_j]
                        model.cbLazy(expr <= len(tour)-1)

def _subtour(edges):
    """Given a list of edges, finds the shortest subtour

    Args:
        edges (:obj: `list`): list of edges. Each edge is written as a tuple (node_i, node_j)
                              where node_i and node_j are strings, eg. ('F-20-28', 'F-20-27')

    Returns:
        shortest_cycle (:obj: `list`): list of all the egdes in the shortest cycle, 
                                       or None if no cycle exists.
    
    Note: algorithm assumes the edges are tuples with int nodes, eg (node_i, node_j) is (1, 3)  
        where node_i and node_j are in range(0,n_nodes). As a consequence, the edges are converted
        using a look up dicts node_to_num and num_to_node 
    """
    nodes = set()
    for node_i, node_j in edges:
        nodes.add(node_i)
        nodes.add(node_j)


    n_nodes = len(nodes)

    # Convert node names to ints, because of alg
    num_to_node = dict()
    node_to_num = dict()
    for i, node in enumerate(nodes):
        num_to_node[i] = node
        node_to_num[node] = i

    edges_nums = list()
    for node_i, node_j in edges:
        edge_nums = node_to_num[node_i], node_to_num[node_j]
        edges_nums.append(edge_nums)

    # algorithm; detecting cycles
    visited = [False]*n_nodes
    cycles = []
    lengths = []
    selected = [[] for i in range(n_nodes)]
    for x,y in edges_nums:
        selected[x].append(y)
    while True:
        current = visited.index(False)
        thiscycle = [current]
        while True:
            visited[current] = True
            neighbors = [x for x in selected[current] if not visited[x]]
            if len(neighbors) == 0:
                break
            current = neighbors[0]
            thiscycle.append(current)
        cycles.append(thiscycle)
        lengths.append(len(thiscycle))
        if sum(lengths) == n_nodes:
            break
        break

    # Delete to short cycles
    indices_to_short_cycles = list()
    for i in range(len(cycles)):
        if len(cycles[i]) < 2:
            indices_to_short_cycles.append(i)
    for i in indices_to_short_cycles:
        cycles.pop(i)
        lengths.pop(i)

    # return None if no cycles
    if len(cycles) is 0:
        return None
    
    # Convert back to original node names
    shortest_cycle_nums = cycles[lengths.index(min(lengths))]
    shortest_cycle_nodes = list()

    for node_num_i in shortest_cycle_nums:
        node = num_to_node[node_num_i]
        shortest_cycle_nodes.append(node)

    # Repeat first node again, to make it start and finish
    shortest_cycle_nodes.append(shortest_cycle_nodes[0])

    # Convert back to list of edges
    shortest_cycle_edges = list()
    for i in range(len(shortest_cycle_nodes)-1):
        if (shortest_cycle_nodes[i], shortest_cycle_nodes[i+1]) in edges:
            egde = shortest_cycle_nodes[i], shortest_cycle_nodes[i+1]
            shortest_cycle_edges.append(egde)
        else:
            edge = shortest_cycle_nodes[i+1], shortest_cycle_nodes[i]
            shortest_cycle_edges.append(egde)

    return shortest_cycle_edges


class Model(gp.Model):
    """This is the warehouse optimization model with uses gurobipy as optimizer.
    
    Attributes:
        gurobi_model (:obj: `gurobipy.Model`): This attribute holds all the information about variables
                                               and solution the optimization problem.
                          _vars (:obj: `dict`): Dictionary with all gurobi.Model variabels.
                                               key: name and item: gurobi.Model var.
                                               eg. __vars['x', 'superscript1', 'subscript1', 'subscript2'] 
                                                   is gurobi_model variable
                     constants (:obj: `dict`): Dictionary with all the constants, ie S.
                                               key: name and item: value (int)
                                               eg. constants['S', 'superscript1', 'subscript1', 'subscript2'] 
                                                   is binary
    
    Note:
        Objective function coefficients are set when variable are set.
        Superscripts are used before subscripts when indexing in dicts.
    """

    def __init__(self, dist, orders, volume=6, max_n_batches=None):
        """
        Args:
            orders (:obj:`dict` of :obj:`infrastructure.Order`): Dict with all orders.
                                                                 key: order_id, item: list of infrastructure.Order.
                                            dist (:obj: `dict`): dict of shortest distances, 
                                                                 between node i and node j, dist['i']['j'].
                                       volume (float, optional): Maximum number of items, ie max volume, that can 
                                                                 fit on a workers tray. If volume is not given (None), 
                                                                 then it will be set to 6 (default).
                                  max_n_batches (int, optional): Maximum number of batches (tours in the warehouse) 
                                                                 that is allowed. If not given (default), ie None, 
                                                                 then it will be set to the ceil of the total number 
                                                                 of orders divided by volume, ie ceil of 
                                                                 num_orders/volume.
        """
        # set none gurobi types
        self._nodes, self._n_picks = self._used_nodes(orders)
        self._constants = self._set_constants(orders, volume, max_n_batches=max_n_batches)

        # set gurobi types
        super().__init__()
        self._vars = self._set_variables(dist, orders)
        self._set_constraints(orders)
        self.params.LazyConstraints = 1 # lazy constraints are used

    def _used_nodes(self, orders):
        """Finds the used nodes and number of picks in the orders input.
        
        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)
        
        Returns:
             nodes (:obj: `list`): list of all node names (str)
                    n_picks (int): total number of picks
        """
        nodes = list()

        nodes.append(NAME_START_NODE)
        nodes.append(NAME_END_NODE)

        n_picks = 0

        for order_id, order in orders.items():
            for pick in order.picks:
                if pick._warehouse_location not in nodes:
                    nodes.append(pick._warehouse_location)
                    n_picks += 1

        return nodes, n_picks

    def _set_constants(self, orders, volume, max_n_batches=None):
        """Sets all constant numbers for Model.
        
        Note:
            Convention: superscripts are used before subscripts when indexing in dicts.
        
        Args:
                    orders (:obj: `dict`): Dict of all orders.
                                           key: order_id (str) and item: (list of infrastructure.Order)
                           volume (float): Maximum number of orders, ie max volume, that can fit on a workers tray.
            max_n_batches (int, optional): Maximum number of batches (tours in the warehouse) that is allowed. 
                                           If not given (default), ie None, then it will be set to the ceil of
                                           the total number of orders divided by volume, 
                                           ie ceil of num_orders/volume.
        
        Returns:
             nodes (:obj: `dict`): dict with all Model constants
                                   key: constant name and item: value (float)
                                   ie. constant['S', 'order_id', 'node'] is binary
        """
        constants = dict()

        # constant VOL
        constants['VOL'] = volume

        # constant max_n_batches
        num_orders = len(orders)
        if max_n_batches is None:
            constants['max_n_batches'] =  math.ceil(num_orders/volume)
        else: 
            constants['max_n_batches'] = max_n_batches


        # constant S
        for order_id in orders:
            for node in self._nodes:
                constants['S', order_id, node] = 0
        for order_id, order in orders.items():
            for pick in order.picks:
                for node in self._nodes:
                    if pick._warehouse_location == node:
                        constants['S', order_id, node] = 1

        return constants

    def _set_variables(self, dist, orders):
        """Initialise all the gurobi variables, and their objective function coefficients.
        
        Note:
            Objective function coefficents, obj=, are also set when variables initialised.
            Default objective value is zero, and will remain so if not other is specified.
            Assuming an undirected graph, is i.e. x_i_j^k equals x_j_i^k (walking direction
            does not matter). Hence we only use x_i_j^k and not x_j_i^k.
        
        Args:
              dist (:obj: `dict`): Dict with distances between nodes, eg dist['node_id_i']['node_id_j']
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)
        
        Returns:
            _vars (:obj: `dict`): Dictionary of variables.
                                 key: id for variable, item: gurobi_model variable
                                 eg. _vars['x', 'superscript1', 'subscript1', 'subscript2'] is gurobipy variable
        """
        _vars = dict()

        # variable: x
        for batch_k in range(self._constants['max_n_batches']):
            for i, node_i in enumerate(self._nodes):
                for node_j in self._nodes[(i+1):]:
                    name = 'x' + '^' + str(batch_k) + '_' + node_i + '_' + node_j
                    _vars['x', batch_k, node_i, node_j] = super().addVar(obj=dist[node_i][node_j],
                                                                         vtype=gp.GRB.BINARY,
                                                                         name=name) 

        # variable: y
        for order in orders:
            for batch in range(self._constants['max_n_batches']):
                name = 'y' + '^' + str(batch) + '_' + str(order)
                _vars['y', batch, order] = super().addVar(vtype=gp.GRB.BINARY, name=name)

        # variable: b
        for batch in range(self._constants['max_n_batches']):
            name = 'b' + '_' + str(batch)
            _vars['b', batch] = super().addVar(vtype=gp.GRB.BINARY, name=name)

        # variable: B
        for batch in range(self._constants['max_n_batches']):
            for node in self._nodes:
                name = 'B' + '^' + str(batch) + '_' + node
                _vars['B', batch, node] = super().addVar(vtype=gp.GRB.BINARY, name=name)

        super().update() # update gurobi model with all vars

        return _vars

    def _set_constraints(self, orders, v_a=1):
        """Initialise all the gurobi constraints apart from the subtour constraint

        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)
            v_a (float, optional): volume per order, default is 1.

        Returns:
            None: it serves as a void function where all the constraint are being set in the Gurobi model
        """
        for batch in range(self._constants['max_n_batches']):
            # Constraint 5 in the Technical Documentation.pdf, "Volume Constraint"
            name = "constraint:" + '5' + ", batch: " + str(batch)
            constraint = \
                sum(v_a * self._vars['y', batch, order] for order in orders) \
                <= self._vars['b', batch] * self._constants['VOL']
            super().addConstr(constraint, name)
            
            # Constraint 3 in the Technical Documentation.pdf, "End to start constraint"
            name = "constraint:" + '3' + ", batch: " + str(batch)
            constraint = self._vars['x', batch, NAME_START_NODE, NAME_END_NODE] == self._vars['b', batch]
            super().addConstr(constraint, name)

            # Constraint 2 in the Technical Documentation.pdf, "Enter and leave constraint"
            node_i = 1
            number_nodes = len(self._nodes)
            for node in self._nodes:
                name = "constraint:" + '2' + ", batch: " + str(batch) + ", node: " + str(node)
                constraint = \
                    sum(self._vars['x', batch, node_l, self._nodes[node_i]] for node_l in self._nodes[:(node_i)]) \
                    + sum(self._vars['x', batch, self._nodes[node_i], node_j] for node_j in self._nodes[(node_i+1):]) \
                    == 2 * self._vars['B', batch, self._nodes[node_i]]
                super().addConstr(constraint, name)
                
                node_i += 1
                if (node_i >= number_nodes):
                    node_i = node_i - 1

        for order in orders:
            # Constraint 6 in the Technical Documentation.pdf, "Pick all orders"
            name = "constraint:" + '6' + ", order: " + str(order)
            constraint = sum(self._vars['y', batch_k, order] for batch_k in range(self._constants['max_n_batches'])) == 1
            super().addConstr(constraint, name)
            #super().update()

            # Constraint 7 in the Technical Documentation.pdf, "Visit node in batch"
            for batch in range(self._constants['max_n_batches']):
                for node in self._nodes:
                    name = "constraint:" + '7' + ", order: " + str(order) + ", batch: " + str(batch) + ", node: " + str(node)
                    constraint = \
                        self._vars['B', batch, node] >= self._vars['y', batch, order] * self._constants['S', order, node]
                    super().addConstr(constraint, name)

        super().update() # update gurobi model with all constraints

    def optimize(self, MIPGap=None):
        """Overwrite optimize function, so that subtour constraints is used.

        Args:
            MIPGap (float, optional): Default value:  1e-4
                                      Minimum value:  0
                                      Maximum value:  Infinity
                                      The MIP solver will terminate (with an optimal result) when 
                                      the gap between the lower and upper objective bound is less than 
                                      MIPGap times the absolute value of the upper bound.
        """
        if MIPGap is not None:
            self.Params.MIPGap = MIPGap
        super().optimize(_subtourelim)

    def solution_batches(self):
        """Temporary function until nice print function is made."""
        solution = super().getAttr('x', self._vars)
        used_nodes = [[] for i in range(self._constants['max_n_batches'])]

        results_string = str()

        for batch in range(self._constants['max_n_batches']):
            for node in self._nodes:
                if solution['B', batch, node] > 0.5:
                    used_nodes[batch].append(node)

            results_string += 'batch: ' + str(batch) + '\t'
            results_string += 'items: ' + str(used_nodes[batch])
            results_string += '\n'

        return results_string


