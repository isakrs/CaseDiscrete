import gurobipy as gp


NAME_START_NODE = "F-20-28"
NAME_END_NODE = "F-20-27"


class Model:
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

    def __init__(self, dist, orders):
        """
        Args:
            orders (:obj:`dict` of :obj:`infrastructure.Order`): Dict with all orders.
                                                                 key: order_id, item: list of infrastructure.Order.
                                            dist (:obj: `dict`): dict of shortest distances, 
                                                                 between node i and node j, dist['i']['j'].

        """
        # set gurobi types
        self.gurobi_model = gp.Model()

        # set none gurobi types
        self._max_n_batches = 1 # TODO: change this to len(orders) or reasonable upper bound on max batches
        self._VOL = self._find_max_order(orders)
        self._nodes, self._n_picks = self._used_nodes(orders)
        self._constants = self._set_constants(orders)
        self._vars = self._set_variables(dist, orders)

        # set model constraints
        self._set_constraints(dist, orders)

    def _find_max_order(self, orders):
        max_order = 0
        for order in orders:
            if (max_order < orders[order].numPicks()):
                max_order = orders[order].numPicks()
        return max_order

    def _used_nodes(self, orders):
        """Finds the used nodes and number of picks in the orders input.

        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)

        Returns:
             nodes (:obj: `list`): list of all node names (str)
                    n_picks (int): total number of picks
        """
        #nodes = set()
        nodes = []

        nodes.append(NAME_START_NODE)
        nodes.append(NAME_END_NODE)

        n_picks = 0

        for order_id, order in orders.items():
            for pick in order.picks:
                nodes.append(pick._warehouse_location)
                n_picks += 1

        return nodes, n_picks

    def _set_constants(self, orders):
        """Sets all constant numbers for Model.

        Note:
            Convention: superscripts are used before subscripts when indexing in dicts.

        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)

        Returns:
             nodes (:obj: `dict`): dict with all Model constants
                                   key: constant name and item: value (float)
                                   ie. constant['S', 'order_id', 'node'] is binary
        """
        constants = dict()

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
        for batch in range(self._max_n_batches):
            for node_i in self._nodes:
                for node_j in self._nodes:
                    name = 'x' + '^' + str(batch) + '_' + node_i + '_' + node_j
                    _vars['x', batch, node_i, node_j] = self.gurobi_model.addVar(obj=dist[node_i][node_j],
                                                                                      vtype=gp.GRB.BINARY,
                                                                                      name=name)
                self.gurobi_model.update()

        # variable: y
        for order in orders:
            for batch in range(self._max_n_batches):
                name = 'y' + '^' + str(batch) + '_' + str(order)
                _vars['y', batch, order] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
            self.gurobi_model.update()

        # variable: b
        for batch in range(self._max_n_batches):
            name = 'b' + '_' + str(batch)
            _vars['b', batch] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
        self.gurobi_model.update()

        # variable: B
        for batch in range(self._max_n_batches):
            for node in self._nodes:
                name = 'B' + '^' + str(batch) + '_' + node
                _vars['B', batch, node] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
            self.gurobi_model.update()

        return _vars

    def _set_constraints(self, dist, orders):
        """Initialize all the constraints"""

        # example from gurobi website and their travelling salesman example
        # Add degree-2 constraint, and forbid loops
        #
        #for i in range(n):
        #    m.addConstr(quicksum(_vars[i,j] for j in range(n)) == 2)
        #    _vars[i,i].ub = 0

        #m.update()


        # Constraint: Enter and leave node ones
        #for batch_i in range(self._max_n_batches):
        #    pass

        #_constraints = {}
        v_a = 1
        node_i = 0

        print(self._VOL)
        for batch in range(self._max_n_batches):
            #Constraint 3.32 in the master thesis
            name = "constraint:" + '5' + ", batch: " + str(batch)
            self.gurobi_model.addConstr(sum(v_a * self._vars['y', batch, order] for order in orders) <= self._vars['b', batch] * self._VOL, name)
            #Constraint 3.30 in the master thesis
            name = "constraint:" + '3,' + ", batch: " + str(batch) 
            self.gurobi_model.addConstr(self._vars['x', batch, NAME_START_NODE, NAME_END_NODE] == self._vars['b', batch], name)
            self.gurobi_model.update()

            node_i = 1
            number_nodes = len(self._nodes)
            for node in self._nodes:
                #Constraint 3.29 in the master thesis
                name = "constraint:" + '2,' + ", batch: " + str(batch) + ", node: " + str(node)
                self.gurobi_model.addConstr(sum(self._vars['x', batch, node_l, self._nodes[node_i]] for node_l in self._nodes[:(node_i-1)])
                                            + sum(self._vars['x', batch, self._nodes[node_i], node_j] for node_j in self._nodes[(node_i+1):])
                                            == 2 * self._vars['B', batch, self._nodes[node_i]], name)
                node_i = node_i + 1
                if (node_i >= number_nodes):
                    node_i = node_i - 1
                self.gurobi_model.update()

        for order in orders:
            #Constraint 3.33 in the master thesis
            name = "constraint:" + '6,' + "order: " + str(order) 
            self.gurobi_model.addConstr(sum(self._vars['y', batch_k, order] for batch_k in range(self._max_n_batches))==1, name)
            print(self._vars['y', self._max_n_batches-1, order])
            self.gurobi_model.update()
            for batch in range(self._max_n_batches):
                for node in self._nodes:
                    #Constraint 3.34 in the master thesis
                    name = "constraint:" + '7,' + "order: " + str(order) + ", batch: " + str(batch) + ", node: " + str(node)
                    """_constraints['7', order, batch, node] = """
                    self.gurobi_model.addConstr(self._vars['B', batch, node] >=
                                                self._vars['y', batch, order] * self._constants['S', order, node], name)
                    self.gurobi_model.update()

