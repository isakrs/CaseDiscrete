from gurobipy import *


class Model:
    def __init__(self, orders, dist):
        self.m = Model()
        self.vars = self._vars(orders, dist)

    def _vars(self, orders, dist):
        

