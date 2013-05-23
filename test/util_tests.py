import logging
import math
import os
import shutil
import sys
import tempfile

from nose.tools import nottest

from fealden.util import Sensor
from fealden import util

logger = logging.getLogger("fealden.util")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def creation_test():
    #    [ [recog, stem1,stem2, repr] ]
    tests = [ ["ATTACC", "CGA", "GAC", "CGAATTACCTCGTGACGGTAATGTC"] ]
    for test in tests:
        sensor = Sensor(test[0])
        sensor.SetStem1(test[1])
        sensor.SetStem2(test[2])
        print("util.Sensor.creation_test: expected 1 got 2\n1:%s\n2:%s" % 
              (test[3],str(sensor)))
        
        assert str(sensor) == test[3]

def Sensor_quencher_index_tests():
    tests = [ ["ATTGC", "", "", 6],
              ["ATTA", "CG", "GC", 9]]

    def _quencher_index_tests(recog, stem1, stem2, expected):
        sensor = Sensor(recog)
        sensor.SetStem1(stem1)
        sensor.SetStem2(stem2)
        print "util.Sensor.quencher_index_tests(%s): expected %s, got %s" % (sensor,
                                                                             test[3],
                                                                             sensor.QuencherIndex())

        assert sensor.QuencherIndex() == test[3]

    for test in tests:
        yield _quencher_index_tests, test[0], test[1], test[2], test[3]

def Sensor_quencher_tests():
    """is util.Sensor properly inserting the quencher?"""
    tests = [ ["ATTGC", "", "", "ATTGCTGCAAT"],
              ["TTTT", "AAA", "AAA", "AAATTTTTTTTAAAAAAATTT"]]



    def _quencher_test(recog, stem1, stem2, expected):
        sensor = Sensor(test[0])
        sensor.SetStem1(test[1])
        sensor.SetStem2(test[2])
        print "util.Sensor.quencher_tests: expected %s, got %s" % (test[3],
                                                                   sensor)

        assert str(sensor) == test[3]

    for test in tests:
        yield _quencher_test, test[0], test[1], test[2], test[3]

def guessstems_tests():
    # [ [ recog, stem1, stem2, guess, repr] ]
    tests = [ ["ATTACC", "CGA", "GAC", "A", "CGAAATTACCTTCGTGACGGTAATGTC"],
              ["ATTACC", "CGAA", "GAC", "T", "CGAAATTACCTTCGTGACTGGTAATAGTC"],
              ["ATTACC", "CGAA", "GACT", "C", "CGAACATTACCGTTCGTGACTGGTAATAGTC"]]
    for test in tests:
        sensor = Sensor(test[0])
        sensor.SetStem1(test[1])
        sensor.SetStem2(test[2])
        sensor.GuessStems(test[3])
    
        print("util.Sensor.guessstems_test: expected 1 got 2\n1:%s\n2:%s" % 
              (test[4],str(sensor)))

        assert str(sensor) == test[4]

def RecognitionEnergy_tests():
    # [ [recognition, free energy] ]
    tests = [ ["CGTA", -2.2],
              ["ATTTATTCG", -5.2]]

    def _recogenergy_test(recog, expected):
        sensor = Sensor(recog)
        print("util.Sensor.RecognitionEnergy_tests: for %s expected %f, got %f" %
              (sensor, expected, sensor.RecognitionEnergy()))

        assert math.fabs(sensor.RecognitionEnergy() - expected) < .01

    for test in tests:
        yield _recogenergy_test, test[0], test[1]


def StemEnergy_tests():
    # [ [stem1, stem2, free energy] ]
    tests = [ ["ATTT", "CGTA", -3.6],
              ["CGAGGGAGAGG", "ATTTATTCG", -14.0]]

    def _stemenergy_test(stem1, stem2, expected):
        sensor = Sensor("")
        sensor.SetStem1(stem1)
        sensor.SetStem2(stem2)

        print("util.Sensor.StemEnergy_tests: for %s expected %f, got %f" %
              (sensor, expected, sensor.StemEnergy()))

        assert math.fabs(sensor.StemEnergy() - expected) < .01

    for test in tests:
        yield _stemenergy_test, test[0], test[1], test[2]

@nottest
def attrib_test_generator():
    tests = [ ["ATTA", "TAAT", "TCG", "CGA",  "CGAA", "TTCG"] ]

    def _attrib_test(recog, recogR, stem1,stem1R, stem2, stem2R):
        sensor = Sensor(recog)
        sensor.SetStem1(stem1)
        sensor.SetStem2(stem2)
        print "_attrib_test(%s, %s, %s)" % (recog, stem1, stem2)

        assert sensor.Recognition == recog
        assert sensor.RecognitionR == recogR
        assert sensor.Stem1 == stem1
        assert sensor.Stem2 == stem2
        assert sensor.Stem1R == stem1R
        assert sensor.Stem2R == stem2R
        
    for test in tests:
        yield(_attrib_test, test[0], test[1], test[2], test[3],
              test[4], test[5])
        

@nottest
def Fold_test_generator():
    def _Fold_switch(seq, recognition, quencher, expected, message):
        
        result = verify.score_switch(seq, recognition, quencher, True)
        print "_score_switch(%s, %s, %d)" % (''.join(seq),
                                             ''.join(recognition),
                                             quencher)
        assert result == expected, ("Test case: %s, Expected %s, Result %s" %
                                    (message, expected, result))


    tests = (
        (list("TACTTTTATATAAATAAGTTGTGATTTTTATATATTTCAC"),list("ATATAAA"),20, (0.414749006915817, 0.46402293676218215, 0.12122805632200077, 0.0), "published case"),
        (list("TTTTGATAAAAAAAAAATTATCTTTT"),list("GATAA"),13, (0.2486820713240543, 0.7513179286759458, 0.0, 0.0), "weighted twoards non-binding"),
        (list("AACTTTTTTGACATACCTCGAAAAAAAGTTAAAAAAACTCGAGGTATGTCGTTTTTTT"), list("GACATACCTCGA"), 30, (0.0, 0.05260134480213224, 0.9473986551978678, 0.0), "Big ugly one"),
        (list("ACTTAGGGGAAGTAACGCCCCTCGTT"), list("AGGGG"),13, (0.34174488499762523, 0.5480807212192699, 0.11017439378310481, 0.0), ""),
        (list(""),list(""),0, (0.0,0.0,0.0,0.0), ""),
        )

    for test in tests:
        yield _score_switch, test[0], test[1], test[2], test[3], test[4]



def DirectoryQueueInit_test_generator():

    def _goodtest(rootdir, directory):
        # Clean up this temp root
        try:
            test_q = util.DirectoryQueue(directory)
        except:
            logger.debug("_goodtest(%s, %s): received unexpected exception %s" %
                  (rootdir, directory, sys.exc_info()[0]))
            # Push this exception back up the stack
            raise
            assert False
        else:
            logger.debug("_goodtest(%s, %s): received no exceptions" %
                  (rootdir, directory))
            assert True
        finally:
            shutil.rmtree(rootdir)

    def _badtest(rootdir, directory, expected):
        try:
            test_q = util.DirectoryQueue(directory)
        except expected:
            logger.debug("_badtest(%s, %s, %s): received expected exception" %
                  (rootdir, directory, expected))
            assert True
        except:
            logger.debug("_badtest(%s, %s, %s): received unexpected exception %s" %
                  (rootdir, directory, expected, sys.exc_info()[0]))
            # Push this exception back up the stack
            raise
            assert False
        else:
            logger.debug("_badtest(%s, %s, %s): received no exceptions" %
                  (rootdir, directory, expected))
            assert False
        finally:
            shutil.rmtree(rootdir)

    tests = ( ("FAIL", "var/fealden/testqueue", util.DirectoryQueueDirectoryError) ,
              ("SUCCESS", "var/fealden/testqueue"))

    for test in tests:
        root = tempfile.mkdtemp()
        dir = os.path.join(root, test[1])
        logger.debug("DirectoryQueue_Init_test_generator(): %s" % dir)
        if test[0] == "FAIL":
            if os.path.isdir(dir):
                shutil.rmtree(dir)
            yield _badtest, root, dir, test[2]
        elif test[0] == "SUCCESS":
            if not os.path.isdir(dir):
                os.makedirs(dir)
            yield _goodtest, root, dir
        else:
            logger.debug("DirectoryQueueInit_test_generator(): WTF, this test"
                  " doesn't make any sense: %s" % test)
            #assert False


def DirectoryQueueRemovingDirectory_init_test():
    
    dir = "/tmp/testqueue"
    # Should not be able to init a queue on a non-existent directory
    try:
        if os.path.isdir(dir):
            shutil.rmtree(dir)
        q = util.DirectoryQueue(dir)
    except util.DirectoryQueueDirectoryError:
        pass
    else:
        logger.debug("BAD - Attempted to create queue, but %s not a directory" %
                     dir)
        assert False 
    finally:
        if os.path.isdir(dir):
            shutil.rmtree(dir)

def DirectoryQueueRemovingDirectory_put_test():
    dir = "/tmp/testqueue"

    os.makedirs(dir)
    try:
        q = util.DirectoryQueue(dir)
        shutil.rmtree(dir)
        q.put(())
    except util.DirectoryQueueDirectoryError:
        logger.debug("GOOD - put on queue with missing directory failed")
        pass
    else:
        logger.debug("BAD - put on queue with missing directory succeeded")
        assert False
    finally:
        if os.path.isdir(dir):
            shutil.rmtree(dir)


def DirectoryQueueRemovingDirectory_get_test():
    dir = "/tmp/testqueue"

    try:
        os.makedirs(dir)
        q = util.DirectoryQueue(dir)
        shutil.rmtree(dir)
        q.get()
    except util.DirectoryQueueDirectoryError:
        logger.debug("GOOD - get on queue with missing directory failed")
        pass
    else:
        logger.debug("BAD - get on queue with missing directory succeeded")
        assert False
    finally:
        if os.path.isdir(dir):
            shutil.rmtree(dir)

def DirectoryQueue_test():
    dir = tempfile.mkdtemp()
    try:
        q = util.DirectoryQueue(dir)

        logger.debug("qsize is %d, expected 0" % q.qsize())
        assert q.qsize() == 0

        test = ("FUCK")
        q.put(test)

        logger.debug("qsize is %d, expected 1" % q.qsize())
        assert q.qsize() == 1

        totest = q.get()
        logger.debug("put %s, got %s" % (test, totest))
        assert test == totest

        for i in range(20):
            q.put(test)

        logger.debug("qsize is %d, expected 1" % q.qsize())
        assert q.qsize() == 20
    finally:
        shutil.rmtree(dir)


def RequestElement_test_generator():
    tests = ( {"command": "BACKTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": -3.4,
               "numsolutions": 1,
               "valid": True,
               "purpose": "all parameters correct"},
              {"command": "BACTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": -3.4,
               "numsolutions": 1,
               "valid": False,
               "purpose": "bad command"},
              {"command": "BACKTRACKING",
               "email": None,
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": None,
               "numfolds_hi": 2,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": -3.4,
               "numsolutions": 1,
               "valid": True,
               "purpose": "only one numfolds set"},
              {"command": "BACKTRACKING",
               "email": None,
               "output_dir": "/tmp/tmp12",
               "maxtime": None,
               "recognition": "ATTA",
               "numfolds_lo": None,
               "numfolds_hi": None,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": "Fuck",
               "numsolutions": 1,
               "valid": False,
               "purpose": "bad maxenergy"},
              {"command": "BACKTRACKING",
               "email": None,
               "output_dir": "ATET%GASFG",
               "maxtime": None,
               "recognition": "ATTA",
               "numfolds_lo": None,
               "numfolds_hi": None,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": None,
               "numsolutions": 1,
               "valid": False,
               "purpose": "malformed directory"},

              {"command": "BACKTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": None,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "maxenergy": -3.4,
               "numsolutions": 1,
               "valid": False,
               "purpose": "binding ratio only hi, no lo"},
              {"command": "BACKTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": 1.5,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": .2,
               "numsolutions": 1,
               "maxenergy": -3.4,
               "valid": False,
               "purpose": "binding ratio lo > hi"},
              {"command": "BACKTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": 1.2,
               "maxunknown_percent": 14123346,
               "numsolutions": 1,
               "maxenergy": -3.4,
               "valid": False,
               "purpose": "max unknown not a percentage"},
              {"command": "BACKTRACKING",
               "email": "test@example.com",
               "output_dir": "/tmp/tmp12",
               "maxtime": 34,
               "recognition": "ATTA",
               "numfolds_lo": 2,
               "numfolds_hi": 2,
               "binding_ratio_lo": 0.8,
               "binding_ratio_hi": None,
               "maxunknown_percent": .2,
               "numsolutions": 1,
               "maxenergy": -3.4,
               "valid": False,
               "purpose": "binding ratio hi, but no lo"},
              )

    def tester(testdict):
        if not os.path.isdir(testdict["output_dir"]):
            os.makedirs(testdict["output_dir"])
 
        testel = util.RequestElement(command=testdict["command"],
                                     email=testdict["email"],
                                     output_dir=testdict["output_dir"],
                                     maxtime=testdict["maxtime"],
                                     recognition=testdict["recognition"],
                                     numfolds_lo=testdict["numfolds_lo"],
                                     numfolds_hi=testdict["numfolds_hi"],
                                     numsolutions=testdict["numsolutions"],
                                     binding_ratio_lo=testdict["binding_ratio_lo"],
                                     binding_ratio_hi=testdict["binding_ratio_hi"],
                                     maxunknown_percent=testdict["maxunknown_percent"],
                                     maxenergy=testdict["maxenergy"])

        if testel.valid() == testdict["valid"]:
            shutil.rmtree(testdict["output_dir"])
            assert True
        else:
            logger.debug("RequestElement_test_generator(): Purpose -- test valid() with %s expected %s, got %s " %
                         (testdict["purpose"], testdict["valid"], testel.valid()))
            shutil.rmtree(testdict["output_dir"])                
            assert False

    for test in tests:
        yield tester, test

def OutputElement_test_generator():
    # (FOUND/FAILED, solution, output_directory, email)
    tests = ( {"command": "WEBOUTPUT",
               "status": "FOUND",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": True,
               "purpose": "valid parameters"},
              {"command": "WEBOUTPUT",
               "status": "FAILED",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": True,
               "purpose": "valid parameters"},
              {"command": "WEBOUTPUT",
               "status": "FAILED",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": "/tmp/shouldnotexist",
               "email": None,
               "valid": False,
               "purpose": "a output_dir does not exist"},
              {"command": "WEBOUTPUT",
               "status": "FAILED",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": None,
               "email": None,
               "valid": False,
               "purpose": "output_dir not specified"},
              {"command": "WEBOUUT",
               "status": "FOUND",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": False,
               "purpose": "invalid command"},
              {"command": "WEBOUTPUT",
               "status": "ND",
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": False,
               "purpose": "command but invalid status"},
              {"command": "WEBOUTPUT",
               "status": False,
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": False,
               "purpose": "command but missing status"},
              {"command": "WEBOUTPUT",
               "status": "FOUND",
               "sensor": True,
               "scores": False,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": False,
               "purpose": "missing scores"},
              {"command": None,
               "status": None,
               "sensor": True,
               "scores": True,
               "folds": True,
               "output_dir": tempfile.mkdtemp(),
               "email": None,
               "valid": False,
               "purpose": "missing command and status"},
)

    def tester(testdict):
        try:
            element = util.OutputElement(command=testdict["command"],
                                                 status=testdict["status"],
                                                 sensor=testdict["sensor"],
                                                 scores=testdict["scores"],
                                                 folds=testdict["folds"],
                                                 output_dir=testdict["output_dir"],
                                                 email=testdict["email"])
        except:
            logger.debug("OutputElementTest(): BAD - init failed with %s" %
                         sys.exc_info()[0])
            raise
            assert False
        else:
            logger.debug("OutputElementTest(): GOOD -- init was fine")

            if element.valid() == testdict["valid"]:
                logger.debug("OutputElementTest(): GOOD -- testing valid() with %s, expected %s, got %s"%
                             (testdict["purpose"], testdict["valid"], element.valid()))
                assert True
            else:
                logger.debug("OutputElementTest(): BAD -- testing valid() with %s, expected %s, got %s"%
                             (testdict["purpose"], testdict["valid"], element.valid()))
                assert False
        finally:
            if testdict["output_dir"] and os.path.isdir(testdict["output_dir"]):
                shutil.rmtree(testdict["output_dir"])

    for test in tests:
        yield tester, test

def SolutionElement_test_generator():
    tests = ( {"command": "SOLUTION",
               "sensor": True,
               "scores": True,
               "request_id": "AFAF",
               "folds": True,
               "depth": -3,
               "purpose": "all good parametsr",
               "valid": True},
              {"command": "SOLUTION",
               "sensor": True,
               "scores": False,
               "request_id": "AFAF",
               "folds": True,
               "depth": None,
               "purpose": "missing scores",
               "valid": False},
              {"command": "SOLUTION",
               "sensor": False,
               "scores": True,
               "request_id": "AFAF",
               "folds": True,
               "depth": None,
               "purpose": "missing sensor",
               "valid": False},
              {"command": "SOLUTION",
               "sensor": True,
               "scores": True,
               "request_id": "AFAF",
               "folds": False,
               "depth": None,
               "purpose": "missing folds",
               "valid": False},
              {"command": "DEPTH",
               "sensor": None,
               "scores": None,
               "request_id": "AFAF",
               "folds": None,
               "depth": 3,
               "purpose": "good depth",
               "valid": True},
              {"command": "DEPTH",
               "sensor": None,
               "scores": None,
               "request_id": "AFAF",
               "folds": None,
               "depth": -3,
               "purpose": "negative depth",
               "valid": False},
              {"command": "DEPTH",
               "sensor": None,
               "scores": None,
               "request_id": "AFAF",
               "folds": None,
               "depth": None,
               "purpose": "missing depth",
               "valid": False},
              {"command": "DEPTH",
               "sensor": None,
               "scores": None,
               "request_id": "AFAF",
               "folds": None,
               "depth": 0,
               "purpose": "depth zero",
               "valid": True},
              {"command": "PRUNED",
               "sensor": None,
               "scores": None,
               "folds": None,
               "request_id": "AFAF",
               "depth": 3,
               "purpose": "good prune",
               "valid": True},
              {"command": "PRUNED",
               "sensor": None,
               "scores": None,
               "folds": None,
               "request_id": "AFAF",
               "depth": -3,
               "purpose": "negative depth for prune",
               "valid": False},
              {"command": "PRUNED",
               "sensor": None,
               "scores": None,
               "folds": None,
               "request_id": "AFAF",
               "depth": 0,
               "purpose": "depth zero for prune",
               "valid": True},
              {"command": "PRUNED",
               "sensor": None,
               "scores": None,
               "folds": None,
               "request_id": "AFAF",
               "depth": None,
               "purpose": "missing depth for prune",
               "valid": False},
              {"command": "@%^^*%@#$%",
               "sensor": None,
               "scores": None,
               "folds": None,
               "request_id": "AFAF",
               "depth": None,
               "purpose": "invalid command",
               "valid": False},
              {"command": "SOLUTION",
               "sensor": True,
               "scores": True,
               "folds": True,
               "depth": -3,
               "request_id": False,
               "purpose": "all good parametrs, but missing request_id",
               "valid": False},
              )

    def tester(testdict):
        try:
            element = util.SolutionElement(command=testdict["command"],
                                           request_id=testdict["request_id"],
                                           sensor=testdict["sensor"],
                                           scores=testdict["scores"],
                                           folds=testdict["folds"],
                                           depth=testdict["depth"])
        except:
            logger.debug("SolutionElementTest(): BAD - init failed with %s" %
                         sys.exc_info()[0])
            raise
            assert False
        else:
            logger.debug("SolutionElementTest(): GOOD -- init was fine")

            if element.valid() == testdict["valid"]:
                logger.debug("SolutionElementTest(): GOOD -- testing valid() with %s, expected %s, got %s"%
                             (testdict["purpose"], testdict["valid"], element.valid()))
                assert True
            else:
                logger.debug("SolutionElementTest(): BAD -- testing valid() with %s, expected %s, got %s"%
                             (testdict["purpose"], testdict["valid"], element.valid()))
                assert False

    for test in tests:
        yield tester, test
