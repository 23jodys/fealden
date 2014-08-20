import logging
import collections

#import orderedset

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def gen_graph(fold):
    """Returns a graph of our fold

       Arguments:
        fold -- as described in unafold
       Returns:
	    a graph as given by Python Patterns -- Implementing Graphs
	    (https://www.python.org/doc/essays/graphs/), each node is a single
            nucleotide index
        """
    def getvertexes(nucl):
        return [x for x in [nucl["bp"], nucl["upstream"],nucl["downstream"]] if x != 0]

    graph = { index + 1: getvertexes(nucl) for (index,nucl) in enumerate (fold)}
    return graph

def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if not graph.has_key(start):
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

def linear(fold, nucl1, nucl2):
    return find_shortest_path(gen_graph(fold), nucl1, nucl2)
