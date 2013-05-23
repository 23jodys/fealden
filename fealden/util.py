import logging
import multiprocessing
import os
import pickle
import tempfile
import time

from fealden import unafold

logger = logging.getLogger('fealden.util')

def complement(seq):
    """Quick helper function to calculate DNA sequence's complement.

    Arguments:
    seq -- list of nucleotides (AGTC) to be complemented

    Given a list of characters represeting a DNA sequence, return
    a list consisting of that strings DNA complment. If a character
    is not a valid DNA nucleotide, return the character unchanged.

    Returns:
    list of nucleotides"""

    pair = {'G': 'C', 'C': 'G','A': 'T','T': 'A'}
    return [pair[nucl] for nucl in seq]

def match(seql, tomatch):
    """Given a sequence and subsequence, return a list of indexes, where
    each index points to a match

    Arguments:
    seql -- list of DNA nucleotides represented as characters to be searched
    tomatch -- list of DNA nucleotides represented as characters to search for

    Returns
    list of DNA nucleotides represented as characters

    Example

    >>> match(list('AAAAAA'), list('AA'))
    [0,1,2,3,4]

    >>> match(list('GCTAATAGCGG'), list('GG'))
    [9]
    """
    
    # list comprehension for each element in seql
    matches = [x for x in range(len(seql)) if seql[x:(x + len(tomatch))] == tomatch]
    return matches

class Sensor:
    """Contains the DNA string for a sensor, as well as all
    structural elements associated with it, e.g. the location of
    stems, loops, flurophore, etc."""

    def __init__(self, recog):
        # Internally, this will be stored as a list
        # Initialize with recognition and set recognition response
        self.Recognition = list(recog)
        self.RecognitionR = complement(self.Recognition)[::-1]
        self.Stem1 = []
        self.Stem1R = []
        self.Stem2 = []
        self.Stem2R = []
        self.Quencher = ["T"]
        self.Antitail = []

    def SetStem1(self, stem1):
        self.Stem1 = list(stem1)
        self.Stem1R = complement(self.Stem1)[::-1]
        return True

    def SetStem2(self, stem2):
        self.Stem2 = list(stem2)
        self.Stem2R = complement(self.Stem2)[::-1]
        return True

    def _FreeEnergy(self, seq):
        """Consider a single DNA list. Then suppose that it was
           bound perfectly to its recognition, then return the
           free energy of that sequence.
    
           Arguments:
           seq -- DNA list
           """

        free_energy = 0

        for i in range(len(seq)):
            if (i == 0 or i == len(seq) - 1):
                if (seq[i] == 'A' or seq[i] == 'T'):
                    free_energy += .1
                elif (seq[i] == 'G' or seq[i] == 'C'):
                    free_energy += .5
            else:
                if (seq[i] == 'A' or seq[i] == 'T'):
                    free_energy += .6
                elif (seq[i] == 'G' or seq[i] == 'C'):
                    free_energy += 1
                    
        return -free_energy

    def QuencherIndex(self):
        """Return the 1-based index of the location of the quencher
        Arguments:
        none

        Returns:
        int 1-based index
        """
        return len(self.Stem1) + len(self.Recognition) + len(self.Stem2) + 1

    def RecognitionEnergy(self):
        """Consider the binding fold (one stem, recognition bound
           to its response) and sum the free energy if the sensor
           were in that ideal form then return that energy.

           Arguments:
           none

           Returns:
           free energy in kJ/mol
           """
        recogenergy = self._FreeEnergy(self.Recognition)
        logger.debug("util.Sensor.RecognitionEnergy(): calculated %f for recognition stems" %
                      recogenergy)
        return recogenergy

    def StemEnergy(self):
        """Consider the nonbinding fold (two stems) and sum
           the free energy if the sensor where in that ideal form
           then return that energy.

           Arguments:
           none

           Returns:
           free energy in kJ/mol
           """

        stemenergy = sum([self._FreeEnergy(stem) for stem in [self.Stem1, self.Stem2]])
        logger.debug("util.Sensor.StemEnergy(): calculated sum of %f for both stems" %
                      stemenergy)
        return stemenergy

    def GetRecognition(self):
        return ''.join(self.Recognition)

    def GuessStems(self, guess):
        """ Given a single letter guess, insert that guess into one
        of the stems and update that stem's recognition.

        Arguments:
        guess -- a single character guess to be inserted

        The algorithm alternates inserting into Stem1 and Stem2,
        consider the table below to see how the sequence is modified
        over subsequent calls

        Guess Stem1 Recognition Stem1R Stem2R RecogonitionR Stem2
        C         C ATGTCTAAT   G             ATTAGACAT      
        C         C ATGTCTAAT   G           G ATTAGACAT     C
        A        AC ATGTCTAAT   GT          G ATTAGACAT     C
        G        AC ATGTCTAAT   GT         CG ATTAGACAT     CG
        G       GAC ATGTCTAAT   GTC        GC ATTAGACAT     CG
        """

        # Consider the length of both stems. If one is less than the other,
        # then insert the guess into the shortest length stem. If they are
        # the same length insert into Stem1
        if len(self.Stem1) > len(self.Stem2):
            self.Stem2.append(guess)
            self.Stem2R = complement(self.Stem2[::-1])
        else:
            self.Stem1.append(guess)
            self.Stem1R = complement(self.Stem1[::-1])
        return True

    def pprint(self):
        """Return something easier to read"""
        return ''.join(self.Stem1 + [" "] + self.Recognition + [" "] +
                       self.Stem1R + [" "] + self.Quencher + [" "] +
                       self.Stem2 + [" "] + self.RecognitionR + [" "] +
                       self.Antitail + [" "] + self.Stem2R)

    def __repr__(self):
        """Return string representation of whole sensor"""
        return ''.join(self.Stem1 + self.Recognition + self.Stem1R +
                       self.Quencher + self.Stem2 + self.RecognitionR +
                       self.Antitail + self.Stem2R)
    
    def __eq__(self, other):
        """Return wether self and other reprsent the same sensor"""
        return True
        
    
class Counter(object):
    """Simple class to implement a shared counter on top of multiprocessing"""
    def __init__(self, initval=0):
        self.val = multiprocessing.RawValue('i', initval)
        self.lock = multiprocessing.Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1
            #print "incrementing to %d" % (self.val.value)
            
    def value(self):
        with self.lock:
            #            print "returning %d" % (self.val.value)
            return self.val.value

class MaxValue(object):
    """Simple class to implement a shared maxdepth on top of multiprocessing"""
    def __init__(self):
        self.val = multiprocessing.RawValue('i', 0)
        self.lock = multiprocessing.Lock()

    def setmax(self,tocheck):
        with self.lock:
            #print "tocheck %d, value %d" % (tocheck, self.val.value)
            if tocheck > self.val.value:
                self.val.value = tocheck
            return self.val.value

    def value(self):
        with self.lock:
            return self.val.value

class SolutionElement():
    """An element to be used in the solution queue utilized by
       sensorsearch.

       Arguments:
       request_id -- a unique id that is specific to a given search
                     request, it is not unique for each solution.
       command -- Required, (SOLUTION|PRUNED|DEPTH)
       sensor -- if command == solution: sensor is required
       scores -- if command == solution: scores is required
       folds -- if command == solution: folds is required
       depth -- if command == (PRUNED|DEPTH): required
                everytime a node is visited its depth is recorded,
                likewise everytime a node is pruned, its depth is
                recorded
       """
    def __init__(self, command, request_id, sensor=None, scores=None,
                 folds=None, depth=None):
        self.request_id = request_id
        self.command = command
        self.sensor = sensor
        self.scores = scores
        self.folds = folds
        self.depth = depth
    def __str__(self):
        if isinstance(self.scores, list):
            scores = len(self.scores)
        else:
            scores = self.scores

        if isinstance(self.folds, list):
            folds = len(self.folds)
        else:
            folds = self.folds

        return ("CMD: %s, len(SENSOR): %s, len(SCORES): %s, len(FOLDS): %s, DEPTH: %s" %
                  (self.command, self.sensor, scores, folds, self.depth))
                  
    def valid(self):
        command = False
        depth = False
        sensor = False
        scores = False
        folds = False
        pruned = False
        request_id = False
        logger.debug("SolutionElement(): %s" % (self))

        if self.request_id:
            request_id = True
        else:
            request_id = False
        
        if self.command=="SOLUTION":
            logger.debug("SolutionElement(): GOOD - CMD: %s is good" % self.command)
            command = True

            if self.sensor:
                logger.debug("SolutionElement(): GOOD - CMD: SOLUTION, has sensor")
                sensor = True
            else:
                logger.debug("SolutionElement(): BAD - CMD: SOLUTION, doesn't have sensor")
                sensor = False

            if self.scores:
                logger.debug("SolutionElement(): GOOD - CMD: SOLUTION, has scores")
                scores = True
            else:
                logger.debug("SolutionElement(): BAD - CMD: SOLUTION, doesn't have scores")
                scores = False

            if self.folds:
                logger.debug("SolutionElement(): GOOD - CMD: SOLUTION, has folds")
                folds = True
            else:
                logger.debug("SolutionElement(): BAD - CMD: SOLUTION, doesn't have folds")
                folds = False
        elif self.command=="PRUNED":
            logger.debug("SolutionElement(): GOOD - CMD: %s is good" % self.command)
            command = True
            if self.depth >= 0:
                logger.debug("SolutionElement(): GOOD - CMD: PRUNED, depth %s >= 0"%
                             self.depth)
                pruned = True
            else:
                logger.debug("SolutionElement(): BAD - CMD: PRUNED, depth %s !>= 0"%
                             self.depth)
                pruned = False
        elif self.command=="DEPTH":
            logger.debug("SolutionElement(): GOOD - CMD: %s is good" % self.command)
            command = True

            if self.depth >= 0:
                logger.debug("SolutionElement(): GOOD - CMD: DEPTH, depth %s >= 0"%
                             self.depth)
                depth = True
            else:
                logger.debug("SolutionElement(): BAD - CMD: DEPTH, depth %s !>= 0"%
                             self.depth)
                depth = False
        else:
            logger.debug("SolutionElement(): GOOD - CMD: %s is good" % self.command)
            command = False

        if request_id and ((command and scores and sensor and folds) or (command and depth) or (command and pruned)):
            return True
        else:
            return False
class OutputElement():
    """An element to used in an output queue.

    Arguments:
    command -- REQUIRED
    status -- REQUIRED
    output_dir -- REQUIRED
    sensor -- Required for (WEBOUTPUT:FOUND), a util.Sensor of the solution
    scores -- Required for (WEBOUTPUT:FOUND), the scores for that sensor
    folds -- Required for (WEBOUTPUT:FOUND), the sensor's foldings
    email -- Optional
    """
    def __init__(self, command, status, output_dir,
                 sensor = None, scores = None,  
                 folds = None, email = None):
        self.command = command
        self.status = status
        self.output_dir = output_dir
        self.sensor = sensor
        self.scores = scores
        self.folds = folds
        self.email = email

    def __str__(self):
        """Returns a human readable version of this request"""
        string = ("CMD: %s, STAT: %s, DIR: %s, SENS: %s, EMAIL: %s, " %
                  (self.command, self.status,
                   self.output_dir, self.sensor,
                   self.email))
        if self.scores:
            string += "len(scores): %d," % len(self.scores)
        if self.folds:
            string += "len(folds) %d" % len(self.folds)

        return string

    def valid(self):
        """Determines if this request is valid, according to the specification
           here

           Arguments:
           None

           Returns:
           True -- if request is valid
           False otherwise
           """
        command = False

        if self.command and self.command == "WEBOUTPUT":
            if self.status and self.status == "FOUND":
                if self.sensor and self.scores and self.folds:
                    logger.debug("OutputElement(): GOOD -- CMD: WEBOUTPUT, STAT: found => sensor, scores, folds")
                    command = True
                else:
                    logger.debug("OutputElement(): BAD -- CMD: WEBOUTPUT, STAT: found but no sensor, scores, folds")
                    command = False
            elif self.status and self.status == "FAILED":
                logger.debug("OutputElement(): GOOD -- CMD: WEBOUTPUT, STAT: failed")
                command = True
            elif self.status:
                logger.debug("OutputElement(): BAD -- CMD: WEBOUTPUT, STAT: %s unknown" %
                             self.status)
                command = False
            else:
                logger.debug("OutputElement(): BAD -- CMD: WEBOUTPUT, no status")
                command = False
        # elif self.command and self.command == "FILEOUTPUT":
        elif self.command:
            logger.debug("OutputElement(): BAD -- CMD: %s, unknown command" %
                         self.command)
            command = False
        else:
            logger.debug("OutputElement(): BAD -- No CMD")
            command = False

        if self.output_dir:
            if os.path.isdir(self.output_dir):
                logger.debug("OutputElement(): GOOD -- output_dir %s exists" %
                             self.output_dir)
                dir = True
            else:
                logger.debug("OutputElement(): BAD -- output_dir %s does not exist" %
                             self.output_dir)
                dir = False
        else:
            logger.debug("OutputElement(): BAD -- no output_dir specified")
            dir = False

        if command and dir:
            return True
        else:
            return False
        
    
class RequestElement():
    def __init__(self, command=None, recognition=None, email=None, maxtime=None,
                 output_dir=None, binding_ratio_lo=None, binding_ratio_hi=None,
                 maxunknown_percent=None, numfolds_lo=None, numfolds_hi=None,
                 maxenergy = None, numsolutions = 1 ):
        """This is a class to contain request for the
           search server to perform search requests

           Arguments:
           command -- Required
           recognition -- Required
           email -- Optional for all
           maxtime -- optional for all
           output_dir -- Required
           numfolds_lo -- Optional, low bound for number of
             foldings in a valid solution
           numfolds_hi -- Optional, high bound for number of
             foldings in a valid solution
           numsolutions -- Optional, defaults to 1
           binding_ratio_lo -- Required, but if included, binding_ratio_hi
             must also be included, it must also be true that
             binding_ratio_lo < binding_ratio_hi
           binding_ratio_hi -- Required, but if included, binding_ratio_hi
             must also be included
           maxunknown_percent -- Optional, 0 <= maxunknown_percent <= 1
           maxenergy -- Optional, the quantity of kJ/mol that the
             most energetic folding in a sensor can exceed the
             free energy released from the recognition binding
             to it's response. Note: this needs to be negative
        """
        self.command = command
        self.recognition = recognition
        self.email = email
        self.maxtime = maxtime
        self.output_dir = output_dir
        self.numfolds_lo = numfolds_lo
        self.numfolds_hi = numfolds_hi
        self.numsolutions = numsolutions
        self.binding_ratio_lo = binding_ratio_lo
        self.binding_ratio_hi = binding_ratio_hi
        self.maxunknown_percent = maxunknown_percent
        self.maxenergy = maxenergy

        self.valid_commands = ["BACKTRACKING"]

    def __str__(self):
        return ("CMD: %s, REC: %s, EMAIL: %s, MAXT: %s, DIR: %s, "
                "LO: %s, HI: %s, MAX: %s" %
                (self.command, self.recognition,
                 self.email, self.maxtime,
                 self.output_dir,
                 self.numfolds_lo, self.numfolds_hi,
                 self.maxenergy))
    def valid(self):
        """Determines if this request is valid, according to the specification
           here

           Arguments:
           None

           Returns:
           True -- if request is valid
           False otherwise
           """

        if self.recognition:
            # Verify that this is in the alphabet requried
            if True:
                logger.debug("RequestElement.valid(): GOOD - recognition %s is valid" %
                             self.recognition)
                recognition = True
            else:
                logger.debug("RequestElement.valid(): BAD - recognition %s is not valid" %
                             self.recognition)
                recognition = False
        else:
            logger.debug("RequestElement.valid(): BAD - no recognition")


            recognition = False

        if self.command:
            if self.command in self.valid_commands:
                logger.debug("RequestElement.valid(): GOOD - command %s is valid" %
                             self.command)
                command = True
            else:
                logger.debug("RequestElement.valid(): BAD - command %s is not valid, not in %s" %
                             (self.command, self.valid_commands))
                command = False
        else:
            logger.debug("RequestElement.valid(): BAD - no command given")
            command = False

        if (self.binding_ratio_lo and self.binding_ratio_hi):
            if (self.binding_ratio_lo < self.binding_ratio_hi):
                logger.debug("RequestElement.valid(): GOOD - %f < %f" %
                             (self.binding_ratio_lo, self.binding_ratio_hi))
                ratio = True
            else:
                logger.debug("RequestElement.valid(): BAD - %f !< %f" %
                             (self.binding_ratio_lo, self.binding_ratio_hi))
                ratio = False
        elif (not self.binding_ratio_lo) and (not self.binding_ratio_hi):
            logger.debug("RequestElement.valid(): GOOD - binding ratio not specificed")
            ratio = True
        else:
            logger.debug("RequestElement.valid(): BAD - binding ratio lo: %s hi: %s" %
                         (self.binding_ratio_lo, self.binding_ratio_hi))
            ratio = False

        if self.output_dir:
            # This test should be a bit stronger, but cie la vie
            if os.path.isabs(self.output_dir) and os.path.isdir(self.output_dir):
                logger.debug("RequestElement.valid(): GOOD - dir %s looks find" %
                             self.output_dir)
                output_dir = True
            else:
                logger.debug("RequestElement.valid(): BAD - dir %s is not a valid directory" %
                             self.output_dir)
                output_dir = False
        else:
            logger.debug("RequestElement.valid(): BAD - no output directory speficied")
            output_dir = False

        if self.maxenergy:
            if isinstance(self.maxenergy,float):
                logger.debug("RequestElement.valid(): GOOD - max energy %f specified and is float" %
                             self.maxenergy)
                maxenergy = True
            else:
                logger.debug("RequestElement.valid(): BAD - max energy %s specified and is something weird" %
                             self.maxenergy)

                maxenergy = False
        else:
            maxenergy = True

        if self.maxunknown_percent:
            if 0 <= self.maxunknown_percent <= 1:
                logger.debug("RequestElement.valid(): GOOD - max unknown 0 <= %f <= 1" %
                             self.maxunknown_percent)
                maxunknown = True
            else:
                logger.debug("RequestElement.valid(): BAD - max unknown 0 !<= %f !<= 1" %
                             self.maxunknown_percent)
                maxunknown = False
        else:
            logger.debug("RequestElement.valid(): GOOD - max unknown percent not specified")
            maxunknown = True

        if command and output_dir and maxenergy and recognition and ratio and maxunknown:
            return True
        else:
            return False
        
class DirectoryQueueDirectoryError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return repr(self.msg)

class DirectoryQueue():
    def __init__(self, directory):
        """Constructor for an unordered queue implmented on top of files
           and directories.  This class pickles objects into files
           contained in directory and implments a queue interface. This is
           *not* threadsafe, since it doesn't manage multiple simultaneous
           get(), although any number of caller's may put() onto the queue
           safely.

        Arguments:
          directory -- directory to store and read queue entries from

        Returns:
          Void
        """
        if not os.path.isdir(directory):
            logger.debug(directory)
            raise DirectoryQueueDirectoryError("%s is not a directory" %
                                               directory)
        self.directory = directory

    def put(self, request):
        """Put an item from the queue. This method is threadsafe. 

           Arguments:
           request -- any pickleable object
        """
        if not os.path.isdir(self.directory):
            raise DirectoryQueueDirectoryError("%s has disappeared, giving up" %
                                               self.directory)

        with tempfile.NamedTemporaryFile(suffix=".dat",
                                         prefix="fealden_request_",
                                         dir=self.directory,
                                         delete=False) as outfile:
        
            pickle.dump(request,outfile)

    def get(self):
        """Returns and removes a request from the queue. This blocks
           until there is an item in the queue. This method is *not*
           threadsafe.

        Arguments:
        None

        Returns:
        the item stored
        """
        if not os.path.isdir(self.directory):
            raise DirectoryQueueDirectoryError("%s has disappeared, giving up" %
                                               self.directory)

        while True:
            files = os.listdir(self.directory)

            if files:
                file = files.pop()
                fullfile = os.path.join(self.directory,file)
                request = pickle.load(open(fullfile))
                os.remove(fullfile)
                return request
            else:
                time.sleep(.1)

    def qsize(self):
        """Returns the size of the queue

        Arguments: None

        Returns:
        a int with the size of the queue

        """
        return len(os.listdir(self.directory))
