import random
import math
import multiprocessing
import logging
import copy
import random
import time
import copy

from fealden.util import *
from fealden import unafold

logger = logging.getLogger('fealden.backtracking')
#logger.setLevel(logging.DEBUG)
#handler = logging.FileHandler("test.log")
#handler.setLevel(logging.DEBUG)
#logger.addHandler(handler)


def sensorsearch(sensor, maxtime, bindingratiorange=(.9,1.1),
               maxunknownpercent=.2, maxsolutions=1, numfoldrange=None, maxenergy=None):
    logger.debug("sensorsearch(%s, %d, %d, %s, %s,%s,%s): has been called as such" %
                 (sensor, maxtime, maxsolutions, bindingratiorange,
                  maxunknownpercent, numfoldrange, maxenergy))

    def _maxtimewatcher(maxtime,command):
        """Acts as a timer. If maxtime seconds elapse, then sets
        command to zero"""
        starttime = time.time()
        endtime = starttime + maxtime
        while True:
            time.sleep(1)
            if time.time() >= endtime:
                logger.info("sensorsearch(...): _maxtimewatcher(%d) time exceeded, stopping search" % maxtime)
                command.value = 0

    recognition_queue = multiprocessing.Queue()
    command = multiprocessing.Value("i", 1)
    maxdepth = 0

    # Start up another process that will asynchronously keep
    # a watch on the overall time, setting the searches to
    # stop when time is exceeded.
    logger.debug("sensorsearch(...): starting maxtimewatcher")
    timep = multiprocessing.Process(target=_maxtimewatcher,
                                    args=(maxtime,command))
    timep.start()

    # Now, launch the backtracking search
    sensor1 = copy.deepcopy(sensor)
    sensor1.GuessStems('T')
    worker1 = multiprocessing.Process(target=checknode,
                                      args=(sensor1, 0,
                                            recognition_queue,
                                            command))
    worker1.start()

    sensor2 = copy.deepcopy(sensor)
    sensor2.GuessStems('G')
    worker2 = multiprocessing.Process(target=checknode,
                                      args=(sensor2, 0,
                                            recognition_queue,
                                            command))
    worker2.start()


    logger.debug("sensorsearch(...): starting checknode worker")

    logger.debug("sensorsearch(...): beggining to loop over recognition_queue")

    pruned = []
    solutions = []
    maxdepth = 0

    while command.value == 1:
        logger.debug("sensorsearch(...): QUEUE -- len(recognition_queue) = %d" %
                     recognition_queue.qsize())

        result = recognition_queue.get(block=True)
        if result[0] == "SOLUTION":
            # Validate solution and if valid append it to
            # our list of solutions
            logger.debug("sensorsearch(...): QUEUE -- SOLUTION(%s, len(scores) = %d, len(folds) = %d)" %
                         (result[1], len(result[2]), len(result[3])))
            if unafold.validate_sensor(result[1], result[2], result[3],
                                       bindingratiorange=bindingratiorange,
                                       maxunknownpercent=maxunknownpercent,
                                       numfoldrange=numfoldrange,
                                       maxenergy=maxenergy):
                logger.debug("sensorsearch(...): QUEUE -- VALID SOLUTION %s" % result[1])
                solutions.append((result[1], result[2], result[3]))
                if len(solutions) == maxsolutions:
                    command.value = 0
                    break
            else:
                logger.debug("sensorsearch(...): QUEUE -- INVALID SOLUTION %s" % result[1])
        elif result[0] == "PRUNE":
            # Add depth to list of nodes pruned
            logger.debug("sensorsearch(...): QUEUE -- PRUNE(%d)" %
                         (result[1]))
            pruned.append(result[1])
        elif result[0] == "DEPTH":
            if result[1] > maxdepth:
                logger.debug("sensorsearch(...): QUEUE -- DEPTH(%d) is now maxdepth "
                             % (result[1]))
                maxdepth = result[1]
            else:
                logger.debug("sensorsearch(...): QUEUE -- DEPTH(%d)"
                             % (result[1]))
        else:
            logger.debug("sensorsearch(...): QUEUE -- UNKNOWN %s" %
                         (result))

    timep.terminate()
    return solutions

def checknode(sensor, depth, recognition_q, command):
    checknode_logger = logging.getLogger('fealden.backtracking.checknode')

    # Order is important here, since we do a depth first
    # search.
    guesses = ["C","A","G","T"]

    # Backtracking algorithms consist of two parts, the first is to
    # determine if a node is "promising", that is, does it contain any
    # characterstics that would preclude *all* of the children of that
    # node from containing valid solutions.

    # If a node is promising, it does not imply that the node is a
    # condidate solution.  Likewise, if a node is a candidate
    # solution, it may not be a candidate solution.

    # Send message indicating what depth we've arrived at
    recognition_q.put(("DEPTH", depth))

    # Check command queue
    #checknode_logger.debug(" checknode(%s, %d): command is %d" % (sensor,command.value)
    if command.value == 0:
        checknode_logger.debug(" checknode(%s, %d): command is 0, returning True" %
                 (sensor, depth))
        return True
    
    #    checknode_logger.debug("backtracking.checknode(%s): this worker is checking its %d node" %
    #                 (sensor, nodecounter.value()))
    #checknode_logger.debug(" checknode(%s, %d): StemEnergy (%f), RecognitionEnergy - 2.0 (%f)" %
    #             (sensor, depth, sensor.StemEnergy(), sensor.RecognitionEnergy() - 2.0))
    if (sensor.StemEnergy() > sensor.RecognitionEnergy() - 2.0):
        # Node is still promising
        checknode_logger.debug(" checknode(%s,%d): PROMISING" %
                      (sensor, depth))

        # Check each child of this node and append any valid solutions
        # from those children
        for guess in guesses:
            checknode_logger.debug(" checknode(%s,%d): checking guess %s" %
                          (sensor, depth, guess))

            # Create new sensor with this guess and recursively check
            # for solutions
            new_sensor = copy.deepcopy(sensor)
            new_sensor.GuessStems(guess)

            checknode(new_sensor, depth + 1, recognition_q, command)

    else:
        # Node is not promising, prune the tree here.
        recognition_q.put(("PRUNE", depth))
        checknode_logger.debug(" checknode(%s,%d): PRUNED" %
                     (sensor, depth))

    # At each node we visit, we will score the sensor and generate
    # all of its foldings and put those scores on recognition queue
    # where another process can evaluate them. 
    folds = unafold.parse_ct(unafold.run_hybrid_ss_min(sensor))
    scores = unafold.score_sensor(sensor,folds)
    
    recognition_q.put(("SOLUTION", sensor, scores, folds))

    return True






    
