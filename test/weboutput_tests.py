from nose.tools import nottest, raises
import tempfile
import os
import pickle
import shutil
import subprocess
from glob import glob

from fealden.lib import weboutput, util

@raises(RuntimeError)
def run_unafold_missing_unafolddir_test():
    # If we call unafold and temp_directory
    # does not exist, then it should throw a
    # RuntimeError
    temp_dir = "/tmp/does_not_exist"
    weboutput.run_unafold(temp_dir, "ATATA")

@raises(RuntimeError)
def run_unafold_bad_permissions_test():
    # If we do not have permissions to write to the UNAfold
    # directory, we need to trhow a runtimeError
    temp_dir = tempfile.mkdtemp()
    subprocess.call(["chmod", "a-w", temp_dir])
    try:
        weboutput.run_unafold(temp_dir, "ATTA")
    finally:
        shutil.rmtree(temp_dir)

@raises(RuntimeError)
def run_unafold_missing_binary_test():
    # Verify that we throw a runtime error if unafold.pl
    # binary is missing.
    bad_command = "/tmp/does_not_exist"
    temp_dir = tempfile.mkdtemp()
    try:
        weboutput.run_unafold(os.path.join("/tmp", "ATTAA"), "ATTAA", bad_command )
    finally:
        shutil.rmtree(temp_dir)


#(unafold_dir, output_dir, convert_cmd="convert")
@raises(RuntimeError)
def convert_substructure_images_no_unafold_dir_test():
    # If we call convert_substructure_images and temp_directory
    # does not exist, then it should throw a
    # RuntimeError
    temp_dir = "/tmp/does_not_exist"
    weboutput.convert_substructure_images(temp_dir, "/tmp")

@raises(RuntimeError)
def convert_substructure_images_bad_permissions_test():
    # If we do not have permissions to write to the unafold
    # directory, we need to trhow a runtimeError
    temp_dir = tempfile.mkdtemp()
    subprocess.call(["chmod", "a-w", temp_dir])
    try:
        weboutput.convert_substructure_images(temp_dir, "/tmp")
    finally:
        shutil.rmtree(temp_dir)

@raises(RuntimeError)
def convert_substructure_images_no_unafold_dir_test():
    # If we call convert_substructure_images and temp_directory
    # does not exist, then it should throw a
    # RuntimeError
    temp_dir = "/tmp/does_not_exist"
    weboutput.convert_substructure_images(temp_dir, "/tmp")

@raises(RuntimeError)
def convert_substructure_images_bad_output_dir_permissions_test():
    testps = """
    %!
    /Helvetica findfont 72 scalefont setfont
    72 72 moveto
    (Hello, world!) show
    showpage
    """
    # If we do not have permissions to write to the output
    # directory, we need to trhow a runtimeError
    output_dir = tempfile.mkdtemp()
    subprocess.call(["chmod", "a-w", output_dir])

    # This function needs to find at least one structure image to
    # convert.
    unafold_dir = tempfile.mkdtemp()
    with open(os.path.join(unafold_dir, "test.ps"), "w") as testpsfile:
       testpsfile.write(testps) 

    try:
        weboutput.convert_substructure_images(unafold_dir, output_dir)
    finally:
        shutil.rmtree(unafold_dir)
        shutil.rmtree(output_dir)

@raises(RuntimeError)
def convert_substructure_images_no_output_dir_test():
    # If we call convert_substructure_images and output_dir
    # does not exist, then it should throw a
    # RuntimeError
    testps = """
    %!
    /Helvetica findfont 72 scalefont setfont
    72 72 moveto
    (Hello, world!) show
    showpage
    """
    output_dir = "/tmp/does_not_exist"

    # This function needs to find at least one structure image to
    # convert.
    unafold_dir = tempfile.mkdtemp()
    with open(os.path.join(unafold_dir, "test.ps"), "w") as testpsfile:
       testpsfile.write(testps) 

    try:
        weboutput.convert_substructure_images(unafold_dir, output_dir)
    finally:
        shutil.rmtree(unafold_dir)


@raises(RuntimeError)
def add_borders_test_no_folds():
    #    def add_borders(folds, output_dir, cmd="/usr/bin/convert")
    add_border_test_file = "./test/tests/add_borders/pngtest16rgba.png"
    folds = []
    sensor = "ATTATATA"

    outputfold_dir = tempfile.mkdtemp()
    try:
        shutil.copy(add_border_test_file, os.path.join(outputfold_dir,"ATTATATA.png"))
        weboutput.add_borders(folds, sensor, outputfold_dir)
    finally:
        shutil.rmtree(outputfold_dir)

@raises(RuntimeError)
def add_borders_test_no_output_dir():
    #    def add_borders(folds, output_dir, cmd="/usr/bin/convert")
    add_border_test_file = "./test/tests/add_borders/pngtest16rgba.png"
    folds = [ { "type": "binding_on" }]
    sensor = "ATTATATA"
    
    outputfold_dir = "/tmp/does_not_exist"

    #shutil.copy(add_border_test_file, os.path.join(outputfold_dir,"ATTATATA.png"))
    # Should raise RuntimeError
    weboutput.add_borders(folds, sensor, outputfold_dir)

@raises(RuntimeError)
def add_borders_test_missing_image_magick():
    #    def add_borders(folds, output_dir, cmd="/usr/bin/convert")
    add_border_test_file = "./test/tests/add_borders/pngtest16rgba.png"
    folds = [ { "type": "binding_on" }]
    #cmd = "/tmp/does_not_exist1"
    sensor = "ATTATATA"

    outputfold_dir = tempfile.mkdtemp()
    
    try:
        shutil.copy(add_border_test_file, os.path.join(outputfold_dir,"ATTATATA.png"))
        weboutput.add_borders(folds, sensor, outputfold_dir)
    finally:
        shutil.rmtree(outputfold_dir)

def add_borders_test_clean():
    #    def add_borders(folds, output_dir, cmd="/usr/bin/convert")
    add_border_test_file = "./test/tests/add_borders/pngtest16rgba.png"
    folds = [ { "type": "binding_on" }]

    sensor = "ATTATATA"

    outputfold_dir = tempfile.mkdtemp()
    
    try:
        shutil.copy(add_border_test_file, os.path.join(outputfold_dir,"ATTATATA_1.png"))
        weboutput.add_borders(folds, sensor, outputfold_dir)
        assert os.path.getsize(os.path.join(outputfold_dir, "ATTATATA_1.png")) > 0
        assert os.path.getsize(os.path.join(outputfold_dir, "ATTATATA_1_t.png")) > 0
    finally:
        shutil.rmtree(outputfold_dir)


# @raises(RuntimeError)
# def convert_substructure_images_bad_unafold_dir_permissions_test():
#     # If we do not have permissions to write to the unafold
#     # directory, we need to trhow a runtimeError
#     temp_dir = tempfile.mkdtemp()
#     subprocess.call(["chmod", "a-w", temp_dir])
#     try:
#         weboutput.convert_substructure_images(temp_dir, "/tmp")
#     finally:
#         shutil.rmtree(temp_dir)


def solution_output_test_generator():
    # tests = [
    #     ["ATTA", 4, [ {"type":"binding_on"}, {"binding_percent":.10}]]
    # ]

    testdir = "./test/tests/solution_output_tests/"
    tests = os.listdir(testdir)

    def _solution_output_tester(sensor, scores, folds):
        badtest = False
        temp_dir = tempfile.mkdtemp()

        weboutput.solution_output(sensor, [], folds, temp_dir)

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
        # Load up sample data
        (sensor, scores, folds) = pickle.load(open(os.path.join(testdir, test, "work", "pickle.dat")))

        yield _solution_output_tester, sensor, scores, folds
