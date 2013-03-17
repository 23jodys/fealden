from nose.tools import nottest
import tempfile
import os
import shutil
from glob import glob

from fealden import weboutput, util

def solution_output_test_generator():
    tests = [
        ["ATTA", 4]
    ]
    
    def _solution_output_tester(sensor, scores, folds):
        badtest = False
        temp_dir = tempfile.mkdtemp()

        weboutput.solution_output(sensor, [],[], temp_dir)

        print("SOLUTION_OUTPUT_TEST: temp dir is %s" % (temp_dir))

        # Test for pickled data
        filename = os.path.join(temp_dir, "pickle.dat")
        size = os.path.getsize(filename)
        if size > 0:
            print (" PICKLE_SIZE: Good, %d bytes" % (size))
        else:
            print (" PICKLE_SIZE: Bad, %d bytes" % (size))
            badtest = True

        #Test for image creation
        for filename in glob(os.path.join(temp_dir, "*_?.png")):
            size = os.path.getsize(filename)
            if size > 0:
                print (" STRUCTURE_IMAGE_SIZE: %d is good" % (size))
            else:
                print(" STRUCTURE_IMAGE_SIZE: %s size is %d" % (filename, size))
                badtest = True

        if badtest:
            assert False
        else:
            # Clean up temp dir if the test passes, otherwise
            # leave them for inspection
            shutil.rmtree(temp_dir)
            assert True

    for test in tests:
        sensor = util.Sensor(test[0])
        yield _solution_output_tester,sensor, [],[]
