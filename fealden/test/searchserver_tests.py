import argparse
import logging
import multiprocessing
import os
import pickle
import Queue
import shutil
import sys
import tempfile

from nose.tools import nottest
from fealden import unafold, util, searchserver

class RequestQueueBacktrackingException(Exception):
    def __init__(self, *args):
        self.msg = args

    def __str__(self):
        return repr(self.msg)

class RequestQueueUnknownException(Exception):
    def __init__(self, *args):
        self.msg = args

    def __str__(self):
        return repr(self.msg)
class SolutionQueueFoundException(Exception):
    def __init__(self, *args):
        self.msg = args

    def __str__(self):
        return repr(self.msg)

class SolutionQueueFailedException(Exception):
    def __init__(self, *args):
        self.msg = args

    def __str__(self):
        return repr(self.msg)
class SolutionQueueUnknownException(Exception):
    def __init__(self, *args):
        self.msg = args

    def __str__(self):
        return repr(self.msg)

def _exception_raiser(toraise):
    def f(*args):
        logger.debug("_exception_raiser(%s): args are %s" %
                     (toraise, args))
        raise toraise()
    return f


logger = logging.getLogger('fealden')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def searchworker_queue_test_generator():
    def _searchworker_tester(request, expectedexception):
        try:
            request_q = Queue.Queue()
            solution_q = Queue.Queue()
            # Set up request dictionary so that the commands raise exceptions
            # rather than calling their designed functions. This tests
            # the queue processing, without actually doing any processing
            msg_dictionary = {'BACKTRACKING': _exception_raiser(RequestQueueBacktrackingException),
                              'UNKNOWN': _exception_raiser(RequestQueueUnknownException)}
            request_q.put(request)
            #request_q.put(("EXIT"))
            print("_searchworker_tester(%s, %s): qsize = %d" %
                  (request.recognition, expectedexception, request_q.qsize()))
            searchserver.searchworker(request_q, solution_q, msg_dictionary)

        except expectedexception:
            print("_searchworker_tester(%s, %s): expected exception received" %
                  (request.recognition, expectedexception))
            assert True
        except:
            print("_searchworker_tester(%s, %s): expected exception not received, instead we got %s" %
                  (request.recognition, expectedexception, sys.exc_info()[0]))
            # reraise the exception
            raise
            assert False
        else:
            print("_searchworker_tester(%s, %s): expected exception %s, but nothing was raised" %
                  (request, expectedexception, expectedexception))
            assert False


    tests = (
        ("BACKTRACKING", "ATTA", "345RTW", "/tmp/test", "test@example.com", 60,RequestQueueBacktrackingException),
        ("BACKDDFD", "ATTA", "345RTW", "/temp/test", "test@example.com", 60,RequestQueueUnknownException),
        ("BACKTRACKING", "ATGCGTATGCGTAAAGTC", "345RTW", "/temp/test", "test@example.com", 60,RequestQueueBacktrackingException))
    
    for test in tests:
        
        request = util.RequestElement(command=test[0],
                                      recognition=test[1],
                                      request_id = test[2],
                                      output_dir=test[3],
                                      email=test[4],
                                      maxtime=test[5])

        yield _searchworker_tester, request, test[6]

def solutionworker_queue_test_generator():
    def _solutionworker_tester(output_request, expectedexception):
        try:
            solution_q = Queue.Queue()
            # Set up cmd dictionary so that the commands raise exceptions
            # rather than calling their designed functions. This tests
            # the queue processing, without actually doing any processing
            cmd_dictionary = {'WEBOUTPUT': _exception_raiser(SolutionQueueFoundException),
                              'UNKNOWN': _exception_raiser(SolutionQueueUnknownException)}

            solution_q.put(output_request)

            print("_solutionworker_tester(%s, %s): qsize = %d" %
                  (output_request, expectedexception, solution_q.qsize()))
            searchserver.solutionworker(solution_q, cmd_dictionary)
        except expectedexception:
            print("_solutionworker_tester(%s, %s): expected exception received" %
                  (output_request, expectedexception))
            assert True
        except:
            print("_solutionworker_tester(%s, %s): expected exception not received, instead we got %s" %
                  (output_request, expectedexception, sys.exc_info()[0]))
            raise
            assert False
        else:
            print("_solutionworker_tester(%s, %s): expected exception %s, but nothing was raised" %
                  (output_request, expectedexception, expectedexception))
            assert False

    # (FOUND/FAILED, solution, output_directory, email)
    tests = (
        ( util.OutputElement(command="WEBOUTPUT", status="FOUND",
                             sensor="ATTCGATATAT", output_dir="/tmp/test/",
                             request_id = "TAGAY56456356",
                             email="test@example.com"),
          SolutionQueueFoundException),)

    for test in tests:
        yield _solutionworker_tester, test[0], test[1]
        


