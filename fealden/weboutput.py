import logging
import math
import tempfile
import os
import glob
import shutil
import pickle
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import itertools

class WebOutputError(Exception):
    """Exception raised for errors in calling some part of
       UNAFold"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


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
    logger = logging.getLogger("fealden.weboutput.solution_output")
    # Run UNAfold in temp dir  on output (or can I do this
    # more directly?)
    logger.info("solution_output(%s, %s): starting output" %
                (sensor, output_dir))
    logger.debug("solution_output(%s, %s): running unafold" %
                 (sensor, output_dir))

    unafold_dir = tempfile.mkdtemp()
    seqfile = open(os.path.join(unafold_dir, str(sensor)),"w")
    seqfile.write(str(sensor))
    seqfile.close()
    command = ['UNAFold.pl','-n','DNA','--temp=25',
               '--sodium=0.15', '--magnesium=0.005',
               '--percent=50', str(sensor)]
    subprocess.call(command,cwd=unafold_dir, stdout=open("/dev/null"))

    # Convert ps -> png for each substructure
    logger.debug("solution_output(%s, %s): converting ps to png" %
                 (sensor, output_dir))

    files = glob.glob(os.path.join(unafold_dir, "*.ps"))
    for ps in files:
        base = os.path.basename(ps)
        name, ext = os.path.splitext(base)
        # Create large png version
        subprocess.call(["convert", ps, os.path.join(output_dir, name + ".png")])

    # Clean up after unafold
    shutil.rmtree(unafold_dir)

    logger.debug("solution_output(%s, %s): creating thumbnails" %
                 (sensor, output_dir))

    # Add borders to each structure image and create thumbnails.
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
        convert_command = ["/usr/bin/convert", "-scale 128x128 -border 10 -bordercolor ", border_color,
                           os.path.join(output_dir, str(sensor) + "_" + str(index + 1) + ".png"),
                           os.path.join(output_dir, str(sensor) + "_" + str(index + 1) + "_t.png")]
        
        subprocess.check_call(' '.join(convert_command), shell=True)

    logger.debug("solution_output(%s, %s): create gain graph" %
                 (sensor, output_dir))

    # Generate sensor gain graph
    binding_kj = sum([ x["percent_in_solution"] *
                       math.exp(x["energy"])
                       for x in folds
                       if x["type"] == "binding_on" or
                       x["type"] == "binding_unknown"])
    nonbinding_kj = sum([ x["percent_in_solution"] * x["energy"]
                          for x in folds
                          if x["type"] == "nonbinding_off" or
                          x["type"] == "badnonbind"])
    logger.debug("solution_output(%s, %s): binding_kj = %f nonbinding_kj = %f" %
              (sensor, output_dir, binding_kj, nonbinding_kj))
    
    plot_gain(binding_kj - nonbinding_kj, sensor, output_dir)
    #sensor_plot.gain(-4.0, seq, output_dir)

    # Pickle output of backtracking search into output_dir
    # The pickled output serves as a signal to the web frontend
    # that the solution has been successfully run.
    logger.debug("solution_output(%s, %s): pickling to output_dir" %
                 (sensor, output_dir))

    pickle.dump((sensor,scores,folds),
                open(os.path.join(output_dir, "pickle.dat"), "w"))

    logger.info("solution_output(%s, %s): finished output" %
                (sensor, output_dir))

    return True


def plot_gain(deltaG, sensor, location="/var/fealden/solutions/", debug=False):
    """Plots the gain of a sensor for different affinities"""
    #debug = True

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

    x = np.logspace(-10, -3, num=50)
    ks = np.e**(-(deltaG / (298 * 0.008314)))

    logger = logging.getLogger("fealden.weboutput.plot_gain")
    logger.debug("sensor_plot.gain(%f, %s, %s): ks calculated as %f" %
              (deltaG, sensor, location, ks))
    
    toplot = np.logspace(-9,-4, 6)

    colors = ['b','g','r','c','m','k']

    for affinity in toplot:
        plt.plot(x, (ks * x)/(affinity * (1+ks) + ks * x), "%s-" % (colors.pop()), label = affinity)
    
    plt.xscale('log')

    ax.legend(loc="center left", bbox_to_anchor=[0.5, 0.5],
               ncol=2, shadow=True, title="Affinity with deltaG = %f" %(deltaG))
    ax.set_xlabel('Transcription Factor Concentration (M)')
    ax.set_ylabel('Predicted Sensor Gain')

    # Uncomment this to display locally, useful for debugging
    #plt.show()

    # Use this to save the image instead
    plt.savefig(os.path.join(location, str(sensor) + "_gain" + ".png"))
    return True

