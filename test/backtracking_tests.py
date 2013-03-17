import Queue
import logging
import multiprocessing

from nose.tools import nottest

#from fealden.util import *
#from fealden.backtracking import *

# @nottest
# def backtracking_checknode_max_recursion_test():
#     """Test backtracking to make sure that it won't
#     go past a certain depth"""
#     #    CCCC TACCG GGGG CCCT CGGTA AGGG
#     tests = [ [ "TACCG", 8] ]


#     logger = logging.getLogger('backtracking')
#     logger.setLevel(logging.INFO)
    

#     for test in tests:
#         solution_q = Queue.Queue()
#         pruned_q = Queue.Queue()
#         maxdepth = MaxValue()
#         nodecounter = Counter()
#         sensor = Sensor(test[0])
#         logging.basicConfig(level=logging.INFO)
#         command = multiprocessing.Value("i", 1)

#         checknode(sensor, 0, solution_q, maxdepth, pruned_q, nodecounter, command)

#         print("backtracking_checknode_max_recursion_test(): for %s, examined %d nodes, found %d solutions" %
#               (sensor, nodecounter.value(), solution_q.qsize()))
#         print("backtracking_checknode_max_recursion_test(): for %s, expected maxdepth %d, got %d" % (sensor, test[1], maxdepth.value()))

#         assert maxdepth.value() == test[1]

# @nottest
# def backtracking_checknode_numnodes_test_generator():
#     tests = [ ["ATTA", "CCC", "CGC", 4 ] ]

#     def _checknode_tester(sensor, numnodes):
#         solutions = multiprocessing.Queue()
#         pruned_q = multiprocessing.Queue()
#         maxdepth = MaxValue()
#         nodecounter = Counter()
#         command = multiprocessing.Value("i", 1)

#         assert _checknode_tester(sensor, test[3])
        
#     for test in tests:
#         sensor = Sensor(test[0])
#         sensor.SetStem1(test[1])
#         sensor.SetStem2(test[2])

#         yield _checknode_tester, sensor, test[3]




