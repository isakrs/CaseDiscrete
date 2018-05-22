import gurobipy as gp


NAME_DEPOT_NODE = ''


class Model:
    """This is the warehouse optimization model with uses gurobipy as optimizer.

    Attributes:
        gurobi_model (:obj: `gurobipy.Model`): This attribute holds all the information about variables
                                               and solution the optimization problem.
                          vars (:obj: `dict`): Dictionary with all gurobi.Model variabels.
                                               key: name and item: gurobi.Model var.
                                               eg. vars['x', 'superscript1', 'subscript1', 'subscript2'] 
                                                   is gurobi_model variable
                     constants (:obj: `dict`): Dictionart with all the constants, ie S.
                                               key: name and item: value (int)
                                               eg. vars['S', 'superscript1', 'subscript1', 'subscript2'] 
                                                   is binary

    Note:
        Convention: superscripts are used before subscripts when indexing in dicts.

    """

    def __init__(self, dist, orders):
        """
        Args:
            orders (:obj:`dict` of :obj:`infrastructure.Order`): Dict with all orders.
                                                                 key: order_id, item: list of infrastructure.Order.
                                            dist (:obj: `dict`): dict of shortest distances, 
                                                                 between node i and node j, dist['i']['j'].

        """
        # gurobi types
        self.gurobi_model = gp.Model()

        # none gurobi types
        self._max_n_batches = 1 # TODO: change this to len(orders) or reasonable upper bound on max batches
        self._nodes, self._n_picks = self._used_nodes(orders)
        self._constants = self._set_constants(orders)
        self.vars = self._set_variables(dist, orders)

    def _used_nodes(self, orders):
        """Finds the used nodes and number of picks in the orders input.

        Args:
            orders (:obj: `dict`): Dict of all orders.
                                   key: order_id (str) and item: (list of infrastructure.Order)

        Returns:
             nodes (:obj: `list`): list of all node names (str)
                    n_picks (int): total number of picks
        """
        nodes = set()

        # TODO: Figure out the name of the depot, or start and end nodes, and makesure it is in dist and self._nodes
        #nodes.add(NAME_DEPOT_NODE)

        n_picks = 0

        for order_id, order in orders.items():
            for pick in order.picks:
                nodes.add(pick._warehouse_location)
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
            vars (:obj: `dict`): Dictionary of variables.
                                 key: id for variable, item: gurobi_model variable
                                 eg. vars['x', 'superscript1', 'subscript1', 'subscript2'] is gurobipy variable
        """
        vars = dict()

        # variable: x
        for batch in range(self._max_n_batches):
            for node_start in self._nodes:
                for node_end in self._nodes:
                    name = 'x' + '^' + str(batch) + '_' + node_start + '_' + node_end
                    vars['x', batch, node_start, node_end] = self.gurobi_model.addVar(obj=dist[node_start][node_end],
                                                                                      vtype=gp.GRB.BINARY,
                                                                                      name=name)
                self.gurobi_model.update()

        # variable: y
        for order in orders:
            for batch in range(self._max_n_batches):
                name = 'y' + '^' + str(batch) + '_' + str(order)
                vars['y', batch, order] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
            self.gurobi_model.update()

        # variable: b
        for batch in range(self._max_n_batches):
            name = 'b' + '_' + str(batch)
            vars['b', batch] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
        self.gurobi_model.update()

        # variable: B
        for batch in range(self._max_n_batches):
            for node in self._nodes:
                name = 'B' + '^' + str(batch) + '_' + node
                vars['B', batch, node] = self.gurobi_model.addVar(vtype=gp.GRB.BINARY, name=name)
            self.gurobi_model.update()

        return vars

    def _constraints(self):
        """Initialize all the constraints"""

        # example from gurobi website and their travelling salesman example
        # Add degree-2 constraint, and forbid loops
        #
        #for i in range(n):
        #    m.addConstr(quicksum(vars[i,j] for j in range(n)) == 2)
        #    vars[i,i].ub = 0

        #m.update()


        # Constraint: Enter and leave node ones
        for batch_i in range(self._max_n_batches):
            pass


