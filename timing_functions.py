from time import time
from copy import deepcopy
from typing import Callable, List
import chess
from move_node import Node


def get_instance_method(instance, method_name) -> Callable:
    """
    Calls 'method_name' on 'instance' if it exists. Raises 'NotImplementedError' otherwise.

    :param instance: A class instance
    :param method_name: The method of 'instance' to call
    :return: The method with name 'method_name'
    """
    try:
        method = getattr(instance, method_name)
        return method
    except AttributeError:
        raise NotImplementedError("Instance of '{}' does not implement method '{};."
                                  .format(instance.__class__.__name__, method_name))


def time_search(node: Node, depth, method_name: str):
    """
    Prints run time for a search function. The last item returned by the test function needs to be the index or list
    of indices.

    :param node: A move node to search
    :param depth: The depth to search
    :param method_name: The name of the method within the Node class
    :raises: :exc:'NotImplementedError' if method_name is not a method of Node class
    """
    node_copy = deepcopy(node)
    search_function = get_instance_method(node_copy, method_name)

    t1 = time()
    *_, index = search_function(depth)
    t2 = time()
    print("Search function '{}' evaluation time: {}s\t{}".format(method_name, round(t2 - t1, 7), index))


def time_score(node: Node, method_name):
    """
    Prints run time for 10,000 calls of a scoring function.

    :param node: A move node to score
    :param method_name: The name of the method within the Node class
    :raises: :exc:'NotImplementedError' if method_name is not a method of Node class
    """
    node_copy = deepcopy(node)
    score_function = get_instance_method(node_copy, method_name)

    t1 = time()
    for i in range(10000):
        _ = score_function()
    t2 = time()
    print("Scoring function '{}' evaluation time: {}s".format(method_name, round(t2 - t1, 7)))
