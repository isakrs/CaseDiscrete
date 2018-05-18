import gurobipy as gp


NAME_DEPOT_NODE = ''


class Model:
    def __init__(self, orders, dist):
        # gurobi types
        self.gurobi_model = gp.Model()

        # none gurobi types
        self._nodes, self._n_picks = self._used_nodes(orders)
        self._vars = self._variables(dist)
        self._max_n_batches = self._n_picks # TODO; upper bound on max_n_batches, to long initializing vars


    def _used_nodes(self, orders):
        nodes = set()
        #nodes.add(NAME_DEPOT_NODE)
        # TODO: Figure out the name of the depot or start and end and make sure it is in the dist and self._nodes

        n_picks = 0

        for order_id, order in orders.items():
            for pick in order.picks:
                nodes.add(pick._warehouse_location)
                n_picks += 1

        return nodes, n_picks


    def _variables(self, dist):
        vars = dict()

        for batch in range(self._max_n_batches):
            for node_start in self._nodes:
                for node_end in self._nodes:
                    name = 'x' + '_' + str(batch) + '_' + node_start + '_' + node_end
                    vars['x', batch, node_start, node_end] = self.gurobi_model.addVar(obj=dist[node_start][node_end],
                                                                                      vtype=gp.GRB.BINARY,
                                                                                      name=name)
                self.gurobi_model.update()

        return vars

    def _constraints_(self):
        """
        # Add degree-2 constraint, and forbid loops

        for i in range(n):
          m.addConstr(quicksum(vars[i,j] for j in range(n)) == 2)
          vars[i,i].ub = 0

        m.update()
        """

        # Constraint: Enter and leave node ones
        for batch_i in range(self._max_n_batches):


