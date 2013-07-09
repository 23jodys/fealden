import glob
import itertools
import logging
import math
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import shutil
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class WebOutputError(Exception):
    """Exception raised for errors in calling some part of
       UNAFold"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

def failed_output(sensor, output_dir, reason):
    logger.error("failed_output(%s, %s) reason: %s" %
                (sensor, output_dir, reason))

    # Attempt to store reason for web app
    try:
        pickle.dump((sensor,reason), open(os.path.join(output_dir, "failed.dat"), "w"))
    except:
        pass


def run_unafold(unafold_dir, sensor, cmd="UNAFold.pl"):
    try:
        seqfile = open(os.path.join(unafold_dir, str(sensor)),"w")
        seqfile.write(str(sensor))
        seqfile.close()
        command = [cmd,'-n','DNA','--temp=25',
                   '--sodium=0.15', '--magnesium=0.005',
                   '--percent=50', str(sensor)]
        subprocess.call(command,cwd=unafold_dir, stdout=open("/dev/null"))
    except (OSError, IOError), err:
        raise RuntimeError(str(err))

def convert_substructure_images(unafold_dir, output_dir, convert_cmd="convert"):
    # Convert ps -> png for each substructure
    
    files = glob.glob(os.path.join(unafold_dir, "*.ps"))
    if len(files) == 0:
        raise RuntimeError("Unable to read any files from %s" % unafold_dir)
    
    try:
        for ps in files:
            base = os.path.basename(ps)
            name, ext = os.path.splitext(base)
            # Create large png version
            torun = [convert_cmd, ps, os.path.join(output_dir, name + ".png")]
            subprocess.check_call(torun, stderr=subprocess.PIPE)
            # if errorcode != 0:
            #     (out,err) = 
            #     raise RuntimeError("convert_substructure_images: %s call failed with errorcode %d" %
            #                        (' '.join(torun), errorcode, ))
    except (OSError, IOError, subprocess.CalledProcessError), err:
        raise RuntimeError(str(err))

def add_borders(folds, sensor, output_dir, cmd="/usr/bin/convert"):
    if len(folds) == 0:
        raise RuntimeError("add_borders(len(%s), %s, %s, %s): called with empty folds" %
                           (len(folds), sensor, output_dir, cmd))
    try:
        for index, fold in enumerate(folds):
            if fold["type"] == "binding_on":
                border_color = "green"
            elif fold["type"] == "nonbinding_off":
                border_color = "blue"
            elif fold["type"] == "binding_unknown":
                border_color == "yellow"
            elif fold["type"] == "nonbinding_unknown":
                border_color == "yellow"
            else:
                border_color = "red"

            # Create thumbnails
            convert_command = [cmd, "-scale 128x128 -border 10 -bordercolor ", border_color,
                               os.path.join(output_dir, str(sensor) + "_" + str(index + 1) + ".png"),
                               os.path.join(output_dir, str(sensor) + "_" + str(index + 1) + "_t.png")]
            subprocess.check_call(' '.join(convert_command), shell=True)
    except (IOError, OSError, subprocess.CalledProcessError), err:
        raise RuntimeError(str(err))

def solution_output(sensor, scores, folds, output_dir):
    """ This output's a ton of information and graphics
        for a validated sensor, to be used by the web
        front end.

    Arguments:
    sensor -- a util.Sensor object
    scores -- a dictionary of the sensor's scores, as output
              by a checknode()
    folds -- a list of all the different folds
    output_dir -- path to directory to output data, it is the
    caller's responsibility to create this safely.

    Returns:
    True, unless error is raised
    """

    # Run UNAfold in temp dir  on output 
    logger.info("solution_output(%s, %s): starting output" %
                (sensor, output_dir))
    logger.debug("solution_output(%s, %s): running unafold" %
                 (sensor, output_dir))
    try:
        unafold_dir = tempfile.mkdtemp()
    except IOError, err:
        logger.error("solution_output(%s, %s): unable to create UNAfold temp directory, permission problem?" %
                     (sensor, output_dir))
        logger.error("   %s" % str(err))
        failed_output(sensor, output_dir, "unable to run UNAfold, permission problem?")
        return False
    try:
        try:
            run_unafold(unafold_dir, sensor)
        except RuntimeError, err:
            logger.error("solution_output(%s, %s): unable to run UNAfold, permission problem or missing binary?" %
                         (sensor, output_dir))
            logger.error("   %s" % str(err))
            failed_output(sensor, output_dir, "unable to run UNAfold, permission problem?")
            return False
        try:
            logger.debug("solution_output(%s, %s): converting ps to png" %
                         (sensor, output_dir))
            convert_substructure_images(unafold_dir, output_dir)
        except RuntimeError, err:
            logger.error("solution_output(%s, %s): unable to convert UNAfold images, permission problem or missing binary?" %
                         (sensor, output_dir))
            logger.error("   %s" % str(err))
            failed_output(sensor, output_dir, "unable to run UNAfold, permission problem?")
            return False
    finally:
        # Clean up after unafold
        shutil.rmtree(unafold_dir)

    # Add borders to each structure image and create thumbnails.
    try:
        logger.debug("solution_output(%s, %s): creating thumbnails" %
                     (sensor, output_dir))
        add_borders(folds, sensor, output_dir)
    except RuntimeError, err:
        logger.error("solution_output(%s, %s): unable to add borders, create thumbnails, permission problem?" %
                     (sensor, output_dir))
        logger.error("   %s" % str(err))
        failed_output(sensor, output_dir, "unable to run process images, permission problem?")
        return False
    # Generate sensor gain graph
    logger.debug("solution_output(%s, %s): create gain graph" %
                 (sensor, output_dir))

    binding_percent = 0
    nonbinding_percent = 0
    for fold in folds:
        if fold["type"] == 'binding_on' or fold["type"] == 'binding_unknown':
            binding_percent += fold["percent_in_solution"]
        elif fold["type"] == 'nonbinding_off' or fold["type"] == 'nonbinding_unknown':
            nonbinding_percent += fold["percent_in_solution"]

    logger.debug("solution_output(%s, %s): binding_percent = %f nonbinding_percent = %f" %
              (sensor, output_dir, binding_percent, nonbinding_percent))
    if nonbinding_percent > 0:
        Ks = binding_percent / nonbinding_percent
    else:
        Ks = 0
    # Plot gain graph
    try:
        plot_gain(Ks, sensor, output_dir)
    except RuntimeError:
        logger.error("solution_output(%s, %s): unable to generate gain graph, permission problem?" %
                     (sensor, output_dir))
        logger.error("   %s" % str(err))
        failed_output(sensor, output_dir, "unable to generate gain graph, permission problem?")
        return False
    # Pickle output of backtracking search into output_dir
    # The pickled output serves as a signal to the web frontend
    # that the solution has been successfully run.
    try:
        logger.debug("solution_output(%s, %s): pickling to output_dir" %
                     (sensor, output_dir))
        pickle.dump((sensor,scores,folds),
                    open(os.path.join(output_dir, "pickle.dat"), "w"))
    except IOError, err:
        logger.error("solution_output(%s, %s): unable to pickle sensor data, permission problem?" %
                     (sensor, output_dir))
        logger.error("   %s" % str(err))
        failed_output(sensor, output_dir, "unable to pickle sensor data, permission problem?")
        return False
    logger.info("solution_output(%s, %s): finished output" %
                (sensor, output_dir))


def plot_gain(Ks, sensor, output_dir):
    """Plots the gain of a sensor for different affinities"""
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

    x = np.logspace(-10, -3, num=50)

    logger.debug("sensor_plot.gain(%f, %s, %s)" %
                (Ks, sensor, output_dir))
    
    toplot = np.logspace(-9,-4, 6)

    colors = ['b','g','r','c','m','k']

    for affinity in toplot:
        plt.plot(x, (Ks * x)/(affinity * (1+Ks) + Ks * x), "%s-" % (colors.pop()), label = affinity)
    
    plt.xscale('log')

    ax.legend(loc="center left", bbox_to_anchor=[0.5, 0.5],
               ncol=2, shadow=True, title="Affinity with K_s = %f" %(Ks))
    ax.set_xlabel('Transcription Factor Concentration (M)')
    ax.set_ylabel('Predicted Sensor Gain')


    try:
        # Uncomment this to display locally, useful for debugging
        # plt.show()
        plt.savefig(os.path.join(output_dir, str(sensor) + "_gain" + ".png"))
    except (IOError), err:
        raise RuntimeError


