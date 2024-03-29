from collections import defaultdict

import numpy as np


class Variable:
    def __init__(self, name, no_states, table, parents=[], no_parent_states=[]):
        """
        name (string): Name of the variable
        no_states (int): Number of states this variable can take
        table (list or Array of reals): Conditional probability table (see below)
        parents (list of strings): Name for each parent variable.
        no_parent_states (list of ints): Number of states that each parent variable can take.

        The table is a 2d array of size #events * #number_of_conditions.
        #number_of_conditions is the number of possible conditions (prod(no_parent_states))
        If the distribution is unconditional #number_of_conditions is 1.
        Each column represents a conditional distribution and sum to 1.

        Here is an example of a variable with 3 states and two parents cond0 and cond1,
        with 3 and 2 possible states respectively.
        +----------+----------+----------+----------+----------+----------+----------+
        |  cond0   | cond0(0) | cond0(1) | cond0(2) | cond0(0) | cond0(1) | cond0(2) |
        +----------+----------+----------+----------+----------+----------+----------+
        |  cond1   | cond1(0) | cond1(0) | cond1(0) | cond1(1) | cond1(1) | cond1(1) |
        +----------+----------+----------+----------+----------+----------+----------+
        | event(0) |  0.2000  |  0.2000  |  0.7000  |  0.0000  |  0.2000  |  0.4000  |
        +----------+----------+----------+----------+----------+----------+----------+
        | event(1) |  0.3000  |  0.8000  |  0.2000  |  0.0000  |  0.2000  |  0.4000  |
        +----------+----------+----------+----------+----------+----------+----------+
        | event(2) |  0.5000  |  0.0000  |  0.1000  |  1.0000  |  0.6000  |  0.2000  |
        +----------+----------+----------+----------+----------+----------+----------+

        To create this table you would use the following parameters:

        Variable('event', 3, [[0.2, 0.2, 0.7, 0.0, 0.2, 0.4],
                              [0.3, 0.8, 0.2, 0.0, 0.2, 0.4],
                              [0.5, 0.0, 0.1, 1.0, 0.6, 0.2]],
                 parents=['cond0', 'cond1'],
                 no_parent_states=[3, 2])
        """
        self.name = name
        self.no_states = no_states
        self.table = np.array(table)
        self.parents = parents
        self.no_parent_states = no_parent_states

        if self.table.shape[0] != self.no_states:
            # raise ValueError(f"Number of states and number of rows in table must be equal.Recieved {self.no_states} number of states, but table has {self.table.shape[0]} number of rows.")
            raise ValueError("feil")
        if self.table.shape[1] != np.prod(no_parent_states):
            raise ValueError("Number of table columns does not match number of parent states combinations.")

        if not np.allclose(self.table.sum(axis=0), 1):
            raise ValueError("All columns in table must sum to 1.")

        if len(parents) != len(no_parent_states):
            raise ValueError("Number of parents must match number of length of list no_parent_states.")

    def __str__(self):
        """
        Pretty string for the table distribution
        For printing to display properly, don't use variable names with more than 7 characters
        """
        width = int(np.prod(self.no_parent_states))
        grid = np.meshgrid(*[range(i) for i in self.no_parent_states])
        s = ""
        for (i, e) in enumerate(self.parents):
            s += '+----------+' + '----------+' * width + '\n'
            gi = grid[i].reshape(-1)
            s += f'|{e:^10}|' + '|'.join([f'{e + "(" + str(j) + ")":^10}' for j in gi])
            s += '|\n'

        for i in range(self.no_states):
            s += '+----------+' + '----------+' * width + '\n'
            state_name = self.name + f'({i})'
            s += f'|{state_name:^10}|' + '|'.join([f'{p:^10.4f}' for p in self.table[i]])
            s += '|\n'

        s += '+----------+' + '----------+' * width + '\n'

        return s

    def probability(self, state, parentstates):
        """
        Returns probability of variable taking on a "state" given "parentstates"
        This method is a simple lookup in the conditional probability table, it does not calculate anything.

        Input:
            state: integer between 0 and no_states
            parentstates: dictionary of {'parent': state}
        Output:
            float with value between 0 and 1
        """
        if not isinstance(state, int):
            raise TypeError(f"Expected state to be of type int; got type {type(state)}.")
        if not isinstance(parentstates, dict):
            raise TypeError(f"Expected parentstates to be of type dict; got type {type(parentstates)}.")
        if state >= self.no_states:
            raise ValueError(f"Recieved state={state}; this variable's last state is {self.no_states - 1}.")
        if state < 0:
            raise ValueError(f"Recieved state={state}; state cannot be negative.")

        table_index = 0
        for variable in self.parents:
            if variable not in parentstates:
                raise ValueError(f"Variable {variable} does not have a defined value in parentstates.")

            var_index = self.parents.index(variable)
            table_index += parentstates[variable] * np.prod(self.no_parent_states[:var_index])

        return self.table[state, int(table_index)]


class BayesianNetwork:
    """
    Class representing a Bayesian network.
    Nodes can be accessed through self.variables['variable_name'].
    Each node is a Variable.

    Edges are stored in a dictionary. A node's children can be accessed by
    self.edges[variable]. Both the key and value in this dictionary is a Variable.
    """

    def __init__(self):
        self.edges = defaultdict(lambda: [])  # All nodes start out with 0 edges
        self.variables = {}  # Dictionary of "name":TabularDistribution

    def add_variable(self, variable):
        """
        Adds a variable to the network.
        """
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected {Variable}; got {type(variable)}.")
        self.variables[variable.name] = variable

    def add_edge(self, from_variable, to_variable):
        """
        Adds an edge from one variable to another in the network. Both variables must have
        been added to the network before calling this method.
        """
        if from_variable not in self.variables.values():
            raise ValueError("Parent variable is not added to list of variables.")
        if to_variable not in self.variables.values():
            raise ValueError("Child variable is not added to list of variables.")
        self.edges[from_variable].append(to_variable)

    def all_edges(self):  # not used help function
        edge_list = []
        for key in self.edges.keys():
            for value in self.edges[key]:
                edge = (key, value)
                edge_list.append(edge)
        return edge_list

    def no_parents(self, variable, edges):  # not used help function
        result = 0
        for edge in edges:
            if edge[1] == variable:
                result += 1
        return result

    def sorted_nodes(self):
        """
        TODO: Implement Kahn's algorithm (or some equivalent algorithm) for putting
              variables in lexicographical topological order.
        Returns: List of sorted variable names.
        """
        l_sorted = []
        s_origin_nodes = []
        variable_names = list(self.variables.keys()).copy()
        variables = []
        edge_dict = self.edges.copy()
        children_of_variable = {}

        for variable_name in variable_names:
            variable = self.variables[variable_name]
            variables.append(variable)
            if not variable.parents:
                s_origin_nodes.append(variable)

        while s_origin_nodes:
            n_parent = s_origin_nodes.pop()
            # print(n_parent.name)
            l_sorted.append(n_parent)

            while edge_dict[n_parent]:
                child_list = edge_dict[n_parent]
                children_of_variable[n_parent] = child_list
                children_of_n = children_of_variable[n_parent]
                # print(len(child_list))
                child = children_of_n[0]
                # print(child.name)
                # print(child_list)
                children_of_n.remove(child)
                # print(child_list)
                for liste in children_of_variable.values():
                    # print(liste)
                    if child in liste:
                        break
                    else:
                        s_origin_nodes.append(child)
                child_list.append(child)

        for variable in variables:
            if children_of_variable[variable]:
                return print("the graph has cycles")
        return l_sorted


class InferenceByEnumeration:
    def __init__(self, bayesian_network):
        self.bayesian_network = bayesian_network
        self.topo_order = bayesian_network.sorted_nodes()

    def normalize(self, query):
        z = sum(query)
        q = [element * 1 / z for element in query]  # now sums to 1
        return q

    def _enumeration_ask(self, X, evidence):
        # TODO: Implement Enumeration-Ask algortihm as described in Problem 4 b)

        query_of_x = []  # distribution of x, but initially empty
        x_variable = self.bayesian_network.variables[X]  # the actual variable x with name X
        vars = self.topo_order

        x_evidence = evidence.copy()
        new_vars = vars.copy()

        for x_state in range(x_variable.no_states):
            query_of_x.insert(x_state, self._enumerate_all(new_vars, x_evidence))
            print(query_of_x)
            x_evidence[x_variable.name] = x_variable

        return self.normalize(query_of_x)

    def get_parents(self, variable):  # returns list of parents-variables
        var_parents = []
        for parent_name in variable.parents:
            var_parents.append(self.bayesian_network.variables[parent_name])
        return var_parents

    def _enumerate_all(self, vars, evidence):
        # TODO: Implement Enumerate-All algortihm as described in Problem 4 b)
        if not vars:
            return 1.0

        y_variable = vars.pop()
        y_parents = self.get_parents(y_variable)
        y_parent_states_dict = {}
        for parent in y_parents:
            y_parent_states_dict[parent] = parent.no_states

        y_evidence = evidence.copy()
        summ = 0

        if y_variable in y_evidence:
            return y_variable.probability(y_variable.no_states, y_evidence) * self._enumerate_all(vars.copy(), y_evidence)
        else:
            for y_state in range(y_variable.no_states):
                summ += y_variable.probability(y_state, evidence) * self._enumerate_all(vars.copy(), y_evidence)
                y_evidence[y_variable.name] = y_variable
            return summ

        """ #First try
        for e in evidence.values()
            if y_variable.value == e: #checks if y (of Y) is in evidence. How??
                known_value = y_variable.value
                return y_variable.probability(known_value, e) 
                * self._enumerate_all(vars.copy(), evidence.values()) # is ? e or y_parent_states_dict 

        for y_state in y_variable.no_states:
            return y_variable.probability(y_state, ?) # ^^
            * self._enumerate_all(vars.copy(), evidence.values())
        """

    def query(self, var, evidence={}):

        # Wrapper around "_enumeration_ask" that returns a
        # Tabular variable instead of a vector
        q = np.array(self._enumeration_ask(var, evidence)).reshape(-1, 1)
        return Variable(var, self.bayesian_network.variables[var].no_states, q)


def problem3c():
    d1 = Variable('A', 2, [[0.8], [0.2]])
    d2 = Variable('B', 2, [[0.5, 0.2],
                           [0.5, 0.8]],
                  parents=['A'],
                  no_parent_states=[2])
    d3 = Variable('C', 2, [[0.1, 0.3],
                           [0.9, 0.7]],
                  parents=['B'],
                  no_parent_states=[2])
    d4 = Variable('D', 2, [[0.6, 0.8],
                           [0.4, 0.2]],
                  parents=['B'],
                  no_parent_states=[2])

    print(f"Probability distribution, P({d1.name})")
    print(d1)

    print(f"Probability distribution, P({d2.name} | {d1.name})")
    print(d2)

    print(f"Probability distribution, P({d3.name} | {d2.name})")
    print(d3)

    print(f"Probability distribution, P({d4.name} | {d2.name})")
    print(d4)

    bn = BayesianNetwork()

    bn.add_variable(d1)
    bn.add_variable(d2)
    bn.add_variable(d3)
    bn.add_variable(d4)
    bn.add_edge(d1, d2)
    bn.add_edge(d2, d3)
    bn.add_edge(d2, d4)

    inference = InferenceByEnumeration(bn)

    #1
    #posterior = inference.query('A', {'C': 1, 'D': 1})
    #print(f"Probability distribution, P({d1.name} | !{d3.name}, {d4.name})")

    #2
    posterior = inference.query('A', {})
    print(f"Probability distribution, P({d1.name})")

    print(posterior)




def monty_hall():
    # TODO: Implement the monty hall problem as described in Problem 4c)
    pass


def main():
    d1 = Variable('A', 2, [[0.8], [0.2]])
    d2 = Variable('B', 2, [[0.5, 0.2],
                           [0.5, 0.8]],
                  parents=['A'],
                  no_parent_states=[2])
    d3 = Variable('C', 2, [[0.1, 0.3],
                           [0.9, 0.7]],
                  parents=['B'],
                  no_parent_states=[2])
    d4 = Variable('D', 2, [[0.6, 0.8],
                           [0.4, 0.2]],
                  parents=['B'],
                  no_parent_states=[2])

    print(f"Probability distribution, P({d1.name})")
    print(d1)

    print(f"Probability distribution, P({d2.name} | {d1.name})")
    print(d2)

    print(f"Probability distribution, P({d3.name} | {d2.name})")
    print(d3)

    print(f"Probability distribution, P({d4.name} | {d2.name})")
    print(d4)

    bn = BayesianNetwork()

    bn.add_variable(d1)
    bn.add_variable(d2)
    bn.add_variable(d3)
    bn.add_variable(d4)
    bn.add_edge(d1, d2)
    bn.add_edge(d2, d3)
    bn.add_edge(d2, d4)

    inference = InferenceByEnumeration(bn)

    #sorted = bn.sorted_nodes()
    #print(sorted)

    # sorted = bn.sorted_nodes()
    sorted = inference.bayesian_network.sorted_nodes()
    print(sorted)


if __name__ == '__main__':
    #problem3c()
    # monty_hall()
    main()