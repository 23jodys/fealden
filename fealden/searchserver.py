import logging
import multiprocessing
import os
import pickle
import tempfile
import time
from fealden import util, backtracking, weboutput

logger = logging.getLogger("fealden.searchserver")

def searchworker(request_q, output_q, cmd_dictionary=None):
    def _request_queue_BACKTRACKING(request, output_q):
        logger.info("searchworker(%d): %s dispatched to _request_queue_BACKTRACKING" %
                    (os.getpid(), request.recognition))
        # Do the search
        sensor = util.Sensor(request.recognition)
        solutions = backtracking.sensorsearch(sensor, request.maxtime,
                                              bindingratiorange = (request.binding_ratio_lo, request.binding_ratio_hi),
                                              maxunknownpercent=request.maxunknown_percent,
                                              numfoldrange=(request.numfolds_lo,request.numfolds_hi),
                                              maxsolutions= request.numsolutions,
                                              maxenergy = request.maxenergy)

        if solutions:
            for solution in solutions:
                # put it on the output_q
                logger.debug("searchworker (%d): found solution for %s" %
                             (os.getpid(),request.recognition))
                # (FOUND/FAILED, solution, output_directory, email)
                output_request = util.OutputElement(command="WEBOUTPUT",
                                                    status="FOUND",
                                                    output_dir= request.output_dir,
                                                    sensor = solution[0],
                                                    scores = solution[1],
                                                    folds = solution[2],
                                                    email = request.email)
                if output_request.valid():
                    output_q.put(output_request)
                else:
                    logger.info("searchworker(%d): attempted to put invalid output_request on to output_q, %s" %
                                output_request)
        else:
            logger.debug("searchworker (%d): no solution for %s" %
                         (os.getpid(), request.recognition))
            output_request = util.OutputElement(command="WEBOUTPUT",
                                           status="FAILED",
                                           output_dir= request.output_dir,
                                           email = request.email)
            output_q.put(output_request)

    def _request_queue_UNKNOWN(request, output_q):
        logger.debug("request_queue: process (%d) reads UNKNOWN, msg is %s" %
                     (os.getpid(),request)),

    logger.debug("searchworker(%d): got this cmd_dict -- %s" %
                 (os.getpid(), cmd_dictionary))
    if not cmd_dictionary:
        cmd_dictionary = {'BACKTRACKING': _request_queue_BACKTRACKING,
                          'UNKNOWN': _request_queue_UNKNOWN}

    # We must have a function associated with "UNKNOWN" 
    assert cmd_dictionary["UNKNOWN"]

    while True:
        request = request_q.get(block=True)

        logger.info("searchworker(%d): got %s for %s" %
                    (os.getpid(), request.command, request.recognition))

        if request.command == "EXIT":
            logger.debug("request_queue(%d): got EXIT" % os.getpid())
            break

        if request.command in cmd_dictionary:
            # If the command is something we have in our
            # message dictionary, then call the function
            # associated with that command
            logger.debug("request_queue(%d): going to attempt to execute %s" %
                         (os.getpid(), cmd_dictionary[request.command]))
            
            cmd_dictionary[request.command](request, output_q)
            #raise cmd_dictionary[request[0]](request[1])
        
        else:
            # Otherwise call the command associated
            # with UNKNOWN
            cmd_dictionary["UNKNOWN"](request, output_q)
            #return True
        #time.sleep(.01)

def solutionworker(output_q,cmd_dictionary=None):
    def _output_queue_UNKNOWN(output_request):
        # Process UNKNOWN messages from a solution queue
        logger.debug("output_queue: process (%d) reads UNKNOWN, msg is %s" %
                     (os.getpid(), msg))
        return True
    
    def _output_queue_WEBOUTPUT(output_request):
        # Generate output for web

        if output_request.status == "FOUND":
            # Process FOUND messages from a solution queue
            logger.info("solutionworker(%d): CMD: WEBOUTPUT STAT: found on %s" %
                        (os.getpid(), output_request.sensor))
            
            weboutput.solution_output(output_request.sensor,
                                      output_request.scores,
                                      output_request.folds,
                                      output_request.output_dir)
            #email_notification(request[0], recognition, request[3])
        elif output_request.status == "FAILED":
            logger.debug("solutionworker (%d): FAILED received for %s" %
                        (os.getpid(), output_request.sensor))
        else:
            logger.debug("solutionworker (%d): I don't know how I got here, %s" %
                        (os.getpid(), output_request))

    if not cmd_dictionary:
        cmd_dictionary = {'WEBOUTPUT': _output_queue_WEBOUTPUT,
                          'UNKNOWN': _output_queue_UNKNOWN}

    # We must have a function associated with "UNKNOWN" 
    assert cmd_dictionary["UNKNOWN"]

    while True:
        output_request = output_q.get(block=True)

        if output_request.command in cmd_dictionary:
            # If the command is something we have in our
            # message dictionary, then call the function
            # associated with that command
            logger.debug("solutionworker(%d): going to attempt to execute %s" %
                         (os.getpid(), cmd_dictionary[output_request.command]))
            cmd_dictionary[output_request.command](output_request)
        else:
            # Otherwise call the command associated
            # with UNKNOWN
            cmd_dictionary["UNKNOWN"](output_request)

def start(request_q, numprocs=1):
    """start -- Starts a pool of workers to process requests
                for searches, another set of workers to
                process validate any solutions found and,
                if valid solutions are found to create suitable
                output for the web version

    Arguments:
    request_q -- a multiprocessing.Queue that will receive
                 requests to be processed from the web application

    Returns:
    True
    """
    # Create solution queue to act as a sink for all
    # of the worker processes.
    # (FOUND/FAILED, output_directory, email, sensor)
    output_q = multiprocessing.Queue()

    # Create pool of wrappers around sensor search that will wait
    # on a request queue and process requests indefinitely
    searchworkers = []
    for i in range(numprocs):
        logger.debug("main loop: starting searchworker %d" % i)
        p = multiprocessing.Process(target=searchworker, args=(request_q, output_q))
        searchworkers.append(p)
        p.start()

    # Start a process to processing the output requests
    logger.debug("main loop: starting solutionworker")
    worker = multiprocessing.Process(target=solutionworker, args=(output_q,))
    worker.start()

