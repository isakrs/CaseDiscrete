import gurobipy as gp
import itertools


NAME_START_NODE = "F-20-28"
NAME_END_NODE = "F-20-27"


def find_subsets(S):
    """Helper function which returns a set of all the subsets of set S.
    Args:
        S (set or array): the set of which you want to output all the subsets.
    Returns:
        set: returns a set of all subsets.
    Example:
    >>> find_subsets(("1" ,"2" ,"3"))
    {'1', ('1', '3'), '3', ('1', '2'), (), ('2', '3'), '2'}
    """
    set_all_subsets = set()

    for i in range(len(S)):
        subset_with_length_i = set(itertools.combinations(S, i))
        
        if (i == 1):
            for element in S:
                set_all_subsets.add(element)
        else:
            for subset in subset_with_length_i:
                set_all_subsets.add(subset)
    
    return set_all_subsets

def _max_order_size(orders):
    """Returns number of items in largest order"""
    max_order_size = 0
    for order in orders:
        if (max_order_size < orders[order].num_picks()):
            max_order_size = orders[order].num_picks()
    return max_order_size

def subtourelim(model, where):
    if where == gp.GRB.callback.MIPSOL:
        
        print('_subtourelim is called')
        for key, content in model._vars.items():
            print('key: ', key, 'content: ', content)
        print('nodes: ', model._nodes)
 
        # for every batch make a list of nodes used in that batch
        used_nodes = [[] for i in range(model._constants['max_n_batches'])]
        for batch_k in range(model._constants['max_n_batches']):
            batch_k_vars = list()
            for i in range(len(model._nodes)-1):
                for j in range(i+1, len(model._nodes)):
                    
                    print('key: ', 'x', batch_k, model._nodes[i], model._nodes[j])
                    
                    var = model._vars['x', batch_k, model._nodes[i], model._nodes[j]]
                    batch_k_vars.append(var)
            sol_batch_k = model.cbGetSolution(batch_k_vars)
            
            print('sol_batch_k: ', sol_batch_k)

                              
                #used_nodes[batch_k] += \
                #    [ (self._nodes[i], self._nodes[j]) \
                #      for j in range(len(self._nodes[i+1:])) \
                #      if sol_batch_k[self._nodes[j]] > 0.5
                #    ]


    """                
        for i in range(n):
            sol = model.cbGetSolution([model._vars[i,j] for j in range(n)])
            selected += [(i,j) for j in range(n) if sol[j] > 0.5]
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < n:
            # add a subtour elimination constraint
            expr = 0
            for i in range(len(tour)):
                for j in range(i+1, len(tour)):
                    expr += model._vars[tour[i], tour[j]]
            model.cbLazy(expr <= len(tour)-1)
    """


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

    def __init__(self, dist, orders, VOL=None, max_n_batches=None):
        """
        Args:
            orders (:obj:`dict` of :obj:`infrastructure.Order`): Dict with all orders.
                                                                 key: order_id, item: list of infrastructure.Order.
                                            dist (:obj: `dict`): dict of shortest distances, 
                                                                 between node i and node j, dist['i']['j'].
                                          VOL (float, optional): Maximum number of items, ie max volume, that can 
                                                                 fit on a workers tray. If VOL is not given (None), 
                                                                 then it will be set to the size of the 
                                                                 largest order (default).
                                  max_n_batches (int, optional): Maximum number of batches (tours in the warehouse) 
                                                                 that is allowed. If not given (default), ie None, 
                                                                 then it will be set to the total number of orders.
        """
        # set none gurobi types
        self._nodes, self._n_picks = self._used_nodes(orders)
        self._constants = self._set_constants(orders, max_n_batches=max_n_batches)

        # set gurobi types
        super().__init__()
        self._vars = self._set_variables(dist, orders)
        self._set_constraints(orders)

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

    def _set_constants(self, orders, VOL=None, max_n_batches=None):
        """Sets all constant numbers for Model.
        Note:
            Convention: superscripts are used before subscripts when indexing in dicts.
        Args:
                    orders (:obj: `dict`): Dict of all orders.
                                           key: order_id (str) and item: (list of infrastructure.Order)
                    VOL (float, optional): Maximum number of items, ie max volume, that can fit on a workers tray.
                                           If VOL is not given (None), then it will be set to the size of the 
                                           largest order.
            max_n_batches (int, optional): Maximum number of batches (tours in the warehouse) that is allowed. 
                                           If not given (default), ie None, then it will be set to 
                                           the total number of orders.
        Returns:
             nodes (:obj: `dict`): dict with all Model constants
                                   key: constant name and item: value (float)
                                   ie. constant['S', 'order_id', 'node'] is binary
        """
        constants = dict()

        # constant VOL
        if VOL is None:
            constants['VOL'] = _max_order_size(orders)
        else:
            constants['VOL'] = VOL

        # constant max_n_batches
        if max_n_batches is None:
            constants['max_n_batches'] = len(orders)
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
        # TODO: Is not this creating an empty last node_j
        for batch_k in range(self._constants['max_n_batches']):
            for i, node_i in enumerate(self._nodes):
                for node_j in self._nodes[(i+1):]:
                    name = 'x' + '^' + str(batch_k) + '_' + node_i + '_' + node_j
                    _vars['x', batch_k, node_i, node_j] = super().addVar(obj=dist[node_i][node_j],
                                                                         vtype=gp.GRB.BINARY,
                                                                         name=name)
                super().update()

        # variable: y
        for order in orders:
            for batch in range(self._constants['max_n_batches']):
                name = 'y' + '^' + str(batch) + '_' + str(order)
                _vars['y', batch, order] = super().addVar(vtype=gp.GRB.BINARY, name=name)
            super().update()

        # variable: b
        for batch in range(self._constants['max_n_batches']):
            name = 'b' + '_' + str(batch)
            _vars['b', batch] = super().addVar(vtype=gp.GRB.BINARY, name=name)
        super().update()

        # variable: B
        for batch in range(self._constants['max_n_batches']):
            for node in self._nodes:
                name = 'B' + '^' + str(batch) + '_' + node
                _vars['B', batch, node] = super().addVar(vtype=gp.GRB.BINARY, name=name)
            super().update()

        return _vars

    def _set_constraints(self, orders):
        """Initialise all the gurobi constraints apart from the subtour constraint
        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)
        Returns:
            None: it serves as a void function where all the constraint are being set in the Gurobi model
        """
        v_a = 1

        for batch in range(self._constants['max_n_batches']):
            # Constraint 3.31 in the master thesis
            set_subsets = find_subsets(self._nodes)
            for subset in set_subsets:
                if subset != ():
                    if (len(subset[0]) == 1):
                        subset = [''.join(subset)]
                        next
                    else:
                        subset = list(subset)

                        name = "constraint:" + '3.31' + ", batch: " + str(batch) + ", subset: " + str(subset)
                        constraint = \
                            sum(sum(self._vars['x', batch, node_i, node_j] \
                            for node_j in subset[(subset.index(node_i)+1):]) for node_i in subset) \
                            <= len(subset) 
                        super().addConstr(constraint, name)
            
            super().update()
            
            # Constraint 3.32 in the master thesis
            name = "constraint:" + '3.32' + ", batch: " + str(batch)
            constraint = \
                sum(v_a * self._vars['y', batch, order] for order in orders) \
                <= self._vars['b', batch] * self._constants['VOL']
            super().addConstr(constraint, name)
            
            # Constraint 3.30 in the master thesis
            name = "constraint:" + '3.30' + ", batch: " + str(batch)
            constraint = self._vars['x', batch, NAME_START_NODE, NAME_END_NODE] == self._vars['b', batch]
            super().addConstr(constraint, name)
            super().update()

            # Constraint 3.29 in the master thesis
            node_i = 1
            number_nodes = len(self._nodes)
            for node in self._nodes:
                name = "constraint:" + '3.29' + ", batch: " + str(batch) + ", node: " + str(node)
                constraint = \
                    sum(self._vars['x', batch, node_l, self._nodes[node_i]] for node_l in self._nodes[:(node_i-1)]) \
                    + sum(self._vars['x', batch, self._nodes[node_i], node_j] for node_j in self._nodes[(node_i+1):]) \
                    == 2 * self._vars['B', batch, self._nodes[node_i]]
                super().addConstr(constraint, name)
                
                node_i += 1
                if (node_i >= number_nodes):
                    node_i = node_i - 1
            super().update()

        for order in orders:
            # Constraint 3.33 in the master thesis
            name = "constraint:" + '3.33' + ", order: " + str(order)
            constraint = sum(self._vars['y', batch_k, order] for batch_k in range(self._constants['max_n_batches'])) == 1
            super().addConstr(constraint, name)
            super().update()

            # Constraint 3.34 in the master thesis
            for batch in range(self._constants['max_n_batches']):
                for node in self._nodes:
                    name = "constraint:" + '3.34' + ", order: " + str(order) + ", batch: " + str(batch) + ", node: " + str(node)
                    constraint = \
                        self._vars['B', batch, node] >= self._vars['y', batch, order] * self._constants['S', order, node]
                    super().addConstr(constraint, name)
                super().update()

    #def optimize():
        """Overwrite optimize function, do that subtour constraints is used."""
