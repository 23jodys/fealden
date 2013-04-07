#!/usr/bin/env python
# Use proper division, rather than C-like floor(div())
from __future__ import division

from types import *

import argparse
import copy
import logging
import math
import operator
import os
import re
import shutil
import subprocess
import sys
import tempfile

import fealden

class UNAFoldError(Exception):
    """Exception raised for errors in calling some part of
       UNAFold"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def run_hybrid_ss_min(sensor, debug=False):
    """Given a sequence, run hybrid-ss-min, return the lines from .ct
       file generated

       Arguments:
       seq -- a list containing the sequence to be folded

       Returns:
       list -- of lines from the .ct file
    """
    tempdir = tempfile.mkdtemp()
    # hybrid-ss-min can only read sequences in from a file and
    # write .ct data to a file, ughh...
    try:
        seqfile = open(os.path.join(tempdir, str(sensor)),"w")
        seqfile.write(str(sensor))
        seqfile.close()
    except IOError:
        raise UNAFoldError("run_hybrid_ss_min(): can't create sequence file")
    command = ['hybrid-ss-min','-n','DNA','--tmin=25', '--tmax=25',
               '--sodium=0.15', '--magnesium=0.005','--mfold=50,-1,100', str(sensor)]

    # Run hybrid-ss-min
    try:
        subprocess.check_call(command,cwd=tempdir, stdout=open("/dev/null"))
    except IOError:
        raise UNAFoldError("run_hybrid_ss_min(): call %s failed" % ' '.join(command))

    # hybrid-ss-min creates a number of files each run, but the $SEQ.ct
    # which contains secondary structure information for each conformation
    # The program ct-energy (part of UNAfold) parses the .ct file and
    # returns an easily parseable secondary structure.

    # Open .ct file
    ct_filename = os.path.join(tempdir, str(sensor) + ".ct")
    ct_file = open(ct_filename)
    if debug: print "run_hybrid_ss_min(): ct_file = %s" % ct_filename

    # read in lines
    lines = ct_file.readlines()

    # Close .ct file
    ct_file.close()

    # UNAfold produces copius output in the form of temporary files
    # So, we must remove all temporary files associated with UNAfold run
    shutil.rmtree(tempdir)

    return lines


def parse_ct(ct_data, debug=False):
    """Return a data structure for all foldings in a .ct file
       from hybrid-ss-min

       Given a list of lines taken from the .ct file output of UNAfold's
       hybrid-ss-min (called with --mfold), return a parsed data
       structure representing all the folds in the .ct file.

       Arguments:
       ct_data: the .ct file represented as a list of lines.

       Returns:
       foldings: list of folds
          each index is a complete fold
          {'fold': [list of dictionaries],
           'energy': (free energy of this fold),
           'type': if the folding is binding_on, nonbinding_off,
                   binding_unknown, or nonbinding_unknown}


          each fold is a list of dictionaries where each
          index of the list refers to the corresponding nucleotide
          in the sequence. At each index a dictionary is stored with
          {'nucl': the nucleotide at this location (A,G,T,C),
           'bp' : number that is the index of nucleotide this
                  forms a base pair with,
           'upstream': index of the nucleotide in the 5' or
                       upstream direction
           'downstream': index of the nucleotide in the 3' or
                       downstream direction,
           'member': What part of the structure this is, Loop1, Loop2,
                     Stem1, Stem2, Tail1, etc...}

       Notes on the .ct file:
       
       Hybrid-ss-min returns all the foldings within a percentage of
       optimal (set in the call to hybrid-ss-min. Then it writes out a
       file with a .ct extension. In this file we have a description
       of every possible folding. 

       The .ct file has any number of foldings contained in it and is
       described in Markham & Zuker 2008

       A fold starts with a line that looks like
       _ n = Number of nucleotides in sequence
       |     _Free energy for this sequence
       |    |               _Name of sequence
       44    dG = -11.989    test

       The number of lines that follow a line of this type is
       precisely the number of nucleotides in the sequence (given in
       that first line)

       Each of these lines has 8 columns
       The ones we care about:
       
       1st column: i, a number indicating that this line is the nth nucleotide
       
       2nd column: What nucleotide is in this position

       3rd column: The 5' or upstream connecting base. Usually i-1,
                   but when i is the 5' base, then it is zero. If i=1
                   and this = n then the nucleic acid is circular
                   (which we don't want)
            
       4th column: The 3' or downstream, same as above, but reverse

       5th column: the index of the matching base pair in this
                   sequence.  0, if this ith nucleotide is not bound
                   (i.e. making a loop of some sort.)

       We want a 'folding' structure that will be a list where each
       index is the corresponding nucleotide position. The ith index
       of the folding structure will refer to a dictionary containing
       the following information

       bp: the index of the base pair or 0
       nucl: the value of the nucleotide here.
       upstream: the 5' base
       downstream: the 3' base
       """
    foldings = []
    fold = []

    for line in ct_data:
        if debug: print "line: %s" % line
        line = line.strip()
        dG_match = re.search(r'(\d*) .* (\W*\S*)', line)
        if dG_match:
            if debug: print "dg_match.group(1): %s, dg_match.group(2):%s" % (dG_match.group(1), dG_match.group(2))
            # We are at a line that starts a folding
            if fold:
                # push the last fold onto folding
                foldings.append({"energy":energy,
                                 "seq":fold})

            # initilize new folding.
            fold = []
            energy = float(dG_match.group(2))

            # Number of nucleotides in this fold
            # (this should be constant, but wtf)
            n = dG_match.group(1)
            
            # Reset structure to be empty
            structure = []
            
        elif line != "":
            # Non-empty lines are part of this folding
            cols = line.split()

            fold.append({"bp": int(cols[4]),
                         "nucl": cols[1],
                         "upstream": int(cols[2]),
                         "downstream": int(cols[3]),
                         "member": ""})

    # Catch the tail end case: if we have a non-empty fold,
    # append it to foldings.
    if fold:
        foldings.append({"energy":energy,
                         "seq":fold,
                         "type":""})
    return foldings


def find_stems(fold, debug=False):
    """Given a fold, look at each nucleotide and determine what
       part of the structure it is a member of: Loop1, Loop2, Stem1,
       etc.

       Arguments:
       fold -- the fold to search for stems in
       ignore_bulge -- boolean to select wether bulge loops are
                       ignored in stems

       Returns: a list of stem dicts
       [
         {'lh':
             {'start': stem1_lh_start,
              'end': stem1_lh_stop},
          'rh':
             {'start': stem1_rh_start,
              'end': stem1_rh_stop},
         },
         {'lh':
             {'start': stem2_lh_start,
              'end': stem2_lh_stop},
          'rh':
             {'start': stem2_rh_start,
              'end': stem2_rh_stop},
         },

         ...
       ]

       """

    stems = []
    loops = []
    tails = []

    n = 1

    lhstempointer_s = 0
    rhstempointer_s = 0
    lhstempointer_e = 0
    rhstempointer_e = 0
    loop_pointer_s = 0
    loop_pointer_e = 0
    counted = []

    for element in fold["seq"]:
        if debug:
            print("find_members(): looking at index %d the middle bp: %d and "
                  "nucl: %s" % (n,element["bp"], element["nucl"]))

        if element["bp"] != 0:
            # members with bp that are non-zero are parts of a stack
            if debug: print " find_members(): bp = %d != 0" % element["bp"]
            if not lhstempointer_s:
                # If lhstem
                if debug:
                    print("  find_members(): Found start of stem, but not "
                          "currently in stem")

                # If we were in a loop, then store it
                if loop_pointer_s:
                    if debug:
                        print("   find_members(): We were in a loop, storing that "
                              "loop, loop_s: %d, loop_e: %d" %
                              (loop_pointer_s, loop_pointer_e))

                    loops.append([loop_pointer_s, loop_pointer_e])
                    loop_pointer_s = 0
                    loop_pointer_e = 0
                # If we have a loop end pointer, but no start pointer,
                # then this was actually a tail, store it.
                if loop_pointer_e and not loop_pointer_s:
                    if debug:
                        print("   find_members(): We have a loop end, but no "
                              "start, storing as a tail")
                    tails.append([loop_pointer_s, loop_pointer_e])
                    loop_pointer_s = 0
                    loop_pointer_e = 0

                # Then start a new stem.
                lhstempointer_s = n
                lhstempointer_e = n
                rhstempointer_s = element["bp"]
                rhstempointer_e = element["bp"]

                # Include n and the bp in counted so we don't double count
                counted.append(n)
                counted.append(element["bp"])
            
            elif lhstempointer_s and element["bp"] == prev - 1:
                # We are currently in a stem *and* the bp is part of
                # decrementing sequence with the previous stem element
                if debug:
                    print("  find_members(): Currently in stem, bp part "
                          "of series")
                lhstempointer_e = n
                rhstempointer_e = element["bp"]
                
                counted.append(n)
                counted.append(element["bp"])
            else:
                # Otherwise this must actually be a new stem
                if debug:
                    print("  find_members(): Part of a stem, but"
                          "  bp != prev - 1. This is a new stem")
                # Store the stem we were working on
                stems.append({"lh":
                              {"start":lhstempointer_s,
                               "end":lhstempointer_e},
                              "rh":
                              {"start":rhstempointer_e,
                               "end":rhstempointer_s}})
                
                # Start a new stem
                lhstempointer_s = n 
                rhstempointer_s = element["bp"]
                lhstempointer_e = n 
                rhstempointer_e = element["bp"]
                counted.append(n)
                counted.append(element["bp"])

                if debug:
                    print("  find_members(): lh_s %d, lh_e %d, "
                          "rh_s %d, lh_s %d" %
                          (lhstempointer_s,
                           lhstempointer_e,
                           rhstempointer_s,
                           rhstempointer_e))
        elif element["bp"] == 0:
                if debug: print " find_members(): bp == 0, in a loop"
                if lhstempointer_s:
                    if debug:
                        print("  find_members(): we were in a stem, "
                              "now in a loop")
                    # We were in a stem, but now we are in a loop, store the
                    # stem
                    stems.append({"lh":
                                  {"start":lhstempointer_s,
                                   "end":lhstempointer_e},
                                  "rh":
                                  {"start":rhstempointer_e,
                                   "end":rhstempointer_s}})
                    lhstempointer_s = 0
                    rhstempointer_s = 0
                    lhstempointer_e = 0
                    rhstempointer_e = 0
                    # And start a loop at this index
                    if debug:
                        print("  find_members(): appending empty list to "
                              "new loop here")
                    loop_pointer_s = n
                    loop_pointer_e = n
                    counted.append(n)
                elif not lhstempointer_s:
                    if debug:
                        print("  find_members(): we were not in a stem, thus we were"
                              " in a loop, still in the loop")
                    # We were not in a stem, therefore we were in a loop,
                    # count this as part of the existing loop
                    loop_pointer_e = n
                    counted.append(n)

                    if debug:
                        print("  find_members(): loop_s: %d loop_e: %d" %
                              (loop_pointer_s, loop_pointer_e))

        if debug:
            print(" find_members(): lh_s %d, lh_e %d, rh_s %d, rh_e %d, "
                  "loop_s %d, loop_e %d" %
                  (lhstempointer_s,
                   lhstempointer_e,
                   rhstempointer_s,
                   rhstempointer_e,
                   loop_pointer_s,
                   loop_pointer_e))
        counted.sort()
        if debug: print " find_members(): counted %s" % str(counted)
        if debug: print " find_members(): stems %s" % str(stems)
        prev = element["bp"]
        n += 1
        if debug: print " find_members(): prev: %d" % prev
    # If we were in a loop when we finished, then the loop was
    # actually a tail
    if loop_pointer_s:
        tails.append([loop_pointer_s, loop_pointer_e])

    # Sometimes a stem is inserted twice, remove these
    seen = []
    for stem in stems:
        if (stem not in seen and
            {"lh": stem["rh"],"rh": stem["lh"]} not in seen):
            seen.append(stem)
    return seen


def combine_stems(left_stems, right_stems, seq_length, depth=0, debug=False):
    """If the folding has bulge loops, merge the stems seperated by bulge
       loops into a single stem.

       Arguments:
       left_stems -- a list of stems, as described in find stems, that contains
                     all of the lefmost stems (5' side). This is a recursive
                     function, so it is first called with the first stem in
                     left_stems 
       right_stems -- a list of stems, as described in find stems, that contains
                     all of the rightmost stems (3' side). This is a recursive
                     function, so it is first called with all the stems *except*
                     the first one.
       seq_length -- int containing the total length of the sequence.
       
       """
    if debug:
        print("combine_stems(%s, %s, %d, %d):" %
              (left_stems, right_stems, seq_length, depth))

    # Bulge loops can contain no more than 20% of the total sequence
    # lenght, if they do, then they aren't bulge loops.
    max_bulge_length = seq_length * .20

    assert len(left_stems) > 0

    if len(right_stems) > 0:
        assert left_stems[-1]["lh"]["end"] < right_stems[0]["lh"]["start"]

    if len(right_stems) < 1:
        # If we have no right_stems, then return left_stems, since there is
        # nothing to join
        if debug:
            print " combine_stems(): %d depth, no more right stems" % depth
        return left_stems
    elif (math.fabs(left_stems[-1]["lh"]["end"] - right_stems[0]["lh"]["start"]) <
          max_bulge_length):
        # The length of this non-bound portion implies that this is a bulge loop
        if debug:
            print(" combine_stems(): %d depth, bulge loop, joining these stems\n"
                  "                : 1st stem end of lh side %d, 2nd stem start of"
                  " lh side %d" % (depth,
                                   left_stems[-1]["lh"]["end"],
                                   right_stems[0]["lh"]["start"]))
        # Join across this non-bound portion
        left_stems[-1]["lh"]["end"] = right_stems[0]["lh"]["end"]
        left_stems[-1]["rh"]["start"] = right_stems[0]["rh"]["start"]
        # Consider the next non-bound portion.
        del right_stems[0]
        return combine_stems(left_stems, right_stems, seq_length, depth + 1, debug)
    else:
        # This is a hairpin, don't join the two stems, but recursively
        # consider the next unbound portion.
        left_stems.append(right_stems[0])
        del right_stems[0]
        if debug:
            print " combine_stems(): %d depth, not a bulge loop, not joining" % depth
        return combine_stems(left_stems, right_stems, seq_length, depth + 1, debug)


def check_recognition_stem(stemlh, stemrh, recognition, debug=False):
    """Given a stem, a recognition sequence to a stem, determine the
       percentage of the recognition expressed in that stem

       Arguments:
       stemlh -- a list containing the left hand side of the stem
       stemrh -- a list containing the right hand (complementary to the lh)
                 side of the stem
       recognition -- a list containing the recognition sequence

       Returns:
       float -- 0.0 - 1.0 that represents the percentage of the recognition
                expressed as largest match divided by length of recognition
       """
    if debug:
        print("check_recognition_stem(): looking for %s with len %d in %s and %s" %
              (''.join(recognition), len(recognition),''.join(stemlh), ''.join(stemrh)))

    # Consider every possible subsequence in recognition by iterating
    # combinatorically through every start index and then for each
    # start index consider each possible length of subsequence from
    # that start for a match in either the lefthand (5') side or
    # righthand (3') side of the stem.
    for start in range(len(recognition)):
        endrng = range(start + 1, len(recognition) + 1)
        endrng.reverse()
        for end in endrng:
            tomatch = recognition[start:end]
            
            if debug:
                print(" check_recognition_stem(): tomatch = %s\n"
                      "                         : lh %s, rh %s" %
                      (''.join(tomatch), ''.join(stemlh), ''.join(stemrh)))
                
                print(" check_recognition_stem(): start %d , end %d" %
                      (start, end))
                print(" check_recognition_stem(): lh match %s" %
                      fealden.util.match(stemlh, tomatch))
                print(" check_recognition_stem(): rh match %s" %
                      fealden.util.match(stemrh, tomatch))
                
            if(fealden.util.match(tuple(stemlh), tuple(tomatch)) or fealden.util.match(tuple(stemlh), tuple(tomatch[::-1])) or
               fealden.util.match(tuple(stemrh), tuple(tomatch)) or fealden.util.match(tuple(stemrh), tuple(tomatch[::-1]))):
                maxlength = float(len(recognition))
                percent = float(end - start) / maxlength
                if debug:
                    print("check_recognition_stem(): found match at len %d,"
                          "start %d, end %d, percent %f" %
                          (len(recognition),start, end, percent))
                return percent
    else:
        # No matches were found
        if debug: print "check_recognition_stem(): no matches found"
        return 0.0

def fluorophore_distance(stem1):
    """Returns distance from the fluorophore to the base
       of stem1, stem2, or the loop between them.

       Arguments:
       stem1 -- a list containing the indexes to the first stem

       Returns:
       int -- distance in nucleotides between the flourophore and
              the base of stem1

       Assumptions:
       1. The fold has precisely two stems.
       2. The fluorophore is at the 5' end
       3. The base of stem1 and stem2, as well as any loop
          connecting them is distance 0
       4. The structure is not circular
       """

    if stem1["lh"]["start"] == 1:
        # Flurophore is at the base of the stack, consider this
        # to be distance 0
        distance = 0
    else:
        # Otherwise count the distance from the base of stem1
        # back towards the end
        distance = stem1["lh"]["start"] - 2
    return distance

def quencher_distance(stem1, stem2 , quencher, debug = False):
    """Returns distance between the quencher and the
       bottom of stem1.

    Arguments:
    stem1 -- a stem dict (as outlined in find_stems())
             with has the indexes to the first stem
    stem2 -- a stem dict (as outlined in find_stems())
             with has the indexes to the second stem
    quencher -- index to location of quencher

    Returns:
    int -- distance in nucleotides between the flourophore and the
           quencher

    Assumptions:
    The fold has precisely two stems.
    """

    assert type(quencher) is IntType

    if debug:
        print("quencher_distance(): quencher index @ %d" % quencher)
        print("quencher_distance(): stem 1 lh %d, %d rh %d, %d" %
              (stem1["lh"]["start"], stem1["lh"]["end"],
               stem1["rh"]["start"], stem1["rh"]["end"]))
        print("quencher_distance(): stem 2 lh %d, %d rh %d, %d" %
              (stem2["lh"]["start"], stem2["lh"]["end"],
               stem2["rh"]["start"], stem2["rh"]["end"]))

    if quencher < stem1["lh"]["start"]:
        # Quencher is in the 5' tail and therefore
        # we use negative distances (since it is
        # that much closer to the fluorophore)
        distance = quencher - stem1["lh"]["start"]
    elif stem1["lh"]["start"] <= quencher <= stem1["lh"]["end"]:
        # Quencher is in the lh side of the 1st stem
        distance = quencher - stem1["lh"]["start"]
    elif stem1["rh"]["start"] <= quencher <= stem1["rh"]["end"]:
        # Quencher is in the rh side of the 1st stem
        distance = stem1["rh"]["end"] - quencher
    elif stem2["lh"]["start"] <= quencher <= stem2["lh"]["end"]:
        # Quencher is in the lh side of the 2nd stem
        # Include in the count, the length of the bulge loop
        # between stem1 and stem2
        distance = (quencher - stem2["lh"]["start"] +
                    stem2["lh"]["start"] - stem1["rh"]["end"])
    elif stem2["rh"]["start"] <= quencher <= stem2["rh"]["end"]:
        # Quencher is in the rh side of the 2st stem
        # Include in the count, the length of the bulge loop
        # between stem1 and stem2
        distance = (stem2["rh"]["end"] - quencher +
                    stem2["lh"]["start"] - stem1["rh"]["end"])
    elif stem1["rh"]["end"] < quencher < stem2["lh"]["start"]:
        # Quencher is in a loop in between the two stems
        # Count distance from bottom of stem1
        distance = quencher - stem1["rh"]["end"]
    else:
        distance =100

    return distance

                   


def fold_type(fold, recognition, quencher, debug=False):
    """Given a fold and a recognition sequence, return its type

       Arguments:
       fold -- a fold structure
       recognition -- a list containing the recognition sequence
       quencher -- an index to the location of the quencher

       Returns:
       str -- One of binding_on/nonbinding_off/binding_unknown/
              nonbinding_unknown

       Notes:
       We care about two different things: wether the fold will
       be likely to bind the recognition (binding/nonbinding) and
       wether the fold will fluoresce (on/off/unknown)

       Binding - Signal On (binding_on)
       Nonbinding - Signal Off (nonbinding_off)
       Binding - Signal Unknown (binding_unknown)
       Nonbinding - Signal Unknown (nonbinding_unknown)

       binding_on
         1. There is precisely one stem, but we can consider
            stems seperated by bulge loops to be one stem.
         2. That stem contains 100% of the recognition sequence
            expressed sequentially

       nonbinding_off
         1. There are precisely two stems, but we can consider
            stems seperated by bulge loops to be one stem.
         2. Both stems contain less than 50% of the recognition
            sequence.
         3. The distance (measured in nucleotides) from the 5' end
            (which contains the fluorophore) and the quencher is 4 or
            less.

       binding_unknown
         1. There may be any number of stems.
         2. At least one of those stems contains more than 50% of the
            recognition sequence expressed sequentially.

       nonbinding_unknown
         1. There may be any number of stems.
         2. None of the stems contain less than 50% of the recognition
            sequence expressed sequentially
    """
    if debug:
        # Define a pretty printer for the stems, if needed
        def pretty_format_stems(stems):
            pretty = ""
            for index,stem in enumerate(stems):
                pretty += (" Stem %d lh: %d,%d rh: %d,%d\n" %
                           (index, stem["lh"]["start"], stem["lh"]["end"],
                            stem["rh"]["start"], stem["rh"]["end"]))
            return pretty

    stems = find_stems(fold, False)

    if (len(stems) == 2 and
        stems[0]["lh"]["start"] < 5 and
        math.fabs(stems[0]["lh"]["end"] -
                  stems[1]["lh"]["start"]) < 5) :
        # If there are two stems and the first stem starts
        # at the beginning of the loop AND there is a bulge
        # loop between stem1 and stem2, then the tails are
        # bound in a stack. Join the two stems, prior to
        # looking for recognition.
        if debug:
            print "fold_type(): tails are bound, combining"
        stems = combine_stems(stems[:1], stems[1:],
                              len(fold["seq"]), 0, debug)

    # Find maximum percentage match for the recognition in all stems
    max_percent_match = 0.0
    for stem in stems:
        match_percent = check_recognition_stem([fold["seq"][n]["nucl"] for
                                               n in range(stem["lh"]["start"] - 1,
                                                          stem["lh"]["end"])],
                                              [fold["seq"][n]["nucl"] for n in
                                               range(stem["rh"]["start"] - 1,
                                                     stem["rh"]["end"])],
                                               recognition, debug)
        if match_percent >  max_percent_match:
            max_percent_match = match_percent

    if debug:
        print("fold_type(): stems\n%s" % pretty_format_stems(stems))
        print("fold_type(): max_percent_match %f , len(stems) %d" %
              (max_percent_match, len(stems)))

    if max_percent_match <= .5:
        # Doesn't look like this will bind to the recognition
        if len(stems) > 2:
            # Attempt to remove bulge loops if we have more than
            # two stems
            if debug:
                print("fold_type(): before joining\n%s" %
                      pretty_format_stems(stems))
            
            stems = combine_stems(stems[:1], stems[1:],
                                  len(fold["seq"]), 0, debug)
            if debug:
                print("fold_type(): after joining\n%s" %
                      pretty_format_stems(stems))
            
        if len(stems) == 2:
            # Now, if we have two stems, find distance between
            # fluorophore and quencher, if possible
            distance = (quencher_distance(stems[0], stems[1],
                                          quencher, debug) +
                        fluorophore_distance(stems[0]))

            if distance < 4:
                if debug:
                    print("fold_type(): distance %d <4, valid nonbinding_off" % distance)
                type = "nonbinding_off"
            else:
                if debug:
                    print "fold_type(): distance %d, nonbinding_unknown" % distance
                type = "nonbinding_unknown"
        else:
            # Not the right number of folds
            if debug: print "fold_type(): too many stems, nonbinding_unknown"
            type = "nonbinding_unknown"
    elif max_percent_match == 1.0:
        # some sort of binding structure
        # Attempt to remove any bulge loops
        stems = combine_stems(stems[:1], stems[1:],
                              len(fold["seq"]), 0, debug)
        if len(stems) == 1:
            type = "binding_on"
        else:
            type = "binding_unknown"
    else:
        # Structures with between 50% and 100% of the recognition
        # may or may not bind to the TF.
        type = "binding_unknown"
    return type


def score_sensor(sensor, folds):
    """Return the scores for a folded sensor

       Arguments:
       sensor -- util.Sensor
       folds -- a folds dict as returned by parse_ct
       
       Returns:
       dictionary = { fold_type: 'percent', ... }
       """

    total = sum([ math.exp(math.fabs(fold["energy"])) for fold in folds])

    for fold in folds:
        fold["type"] = fold_type(fold, sensor.Recognition, sensor.QuencherIndex())
        fold["percent_in_solution"] = math.exp(math.fabs(fold["energy"])) / total

    scores = { "binding_on": { "percent": sum([fold["percent_in_solution"]
                                               for fold in folds
                                               if fold["type"] == 'binding_on']),
                               "num": len([fold for fold in folds
                                           if fold["type"] == 'binding_on'])},
               "nonbinding_off": {"percent": sum([fold["percent_in_solution"]
                                               for fold in folds
                                               if fold["type"] == 'nonbinding_off']),
                               "num": len([fold["percent_in_solution"]
                                           for fold in folds
                                           if fold["type"] == 'nonbinding_off'])},
               "binding_unknown": {"percent": sum([fold["percent_in_solution"]
                                                   for fold in folds
                                                   if fold["type"] == 'binding_unknown']),
                                   "num":len([fold["percent_in_solution"]
                                              for fold in folds
                                              if fold["type"] == 'binding_unknown'])},
               "nonbinding_unknown": {"percent": sum([fold["percent_in_solution"]
                                                      for fold in folds
                                                      if fold["type"] == 'nonbinding_unknown']),
                                      "num": len([fold["percent_in_solution"]
                                                  for fold in folds
                                                  if fold["type"] == 'badnonbind'])}
               }

    return scores

def validate_sensor(sensor, scores, folds, bindingratiorange=(.9,1.1),
                    maxunknownpercent=.2, numfoldrange=None, maxenergy=None):
    """
    Determines if a given sensor is a valid solution

    Arguments:
    sensor -- a util.Sensor
    scores -- as returned by unafold.score_sensor
    folds -- as returned by unafold.parse_ct
    bindingratiorange  -- A tuple containing the min and max of the ratio of
                          binding folds to non-binding folds as determined by
                          the percent in solution of each
    maxunknownpercent -- Maximum percentage of unknown folds in solution
    numfoldrange -- A tuple containing the min and max number of folds in
                    the structure. A value of None indicates that this parameter
                    may be ignored.
    maxenergy -- Consider each sensor, there is a minimal
                 free energy that must be released, derived from the 
                 the recognition and its response that determines the
                 minimal free energy of *any* fold in the sensor. If the given
                 sensor contains a fold where the free energy exceeds the
                 minimal energy by the quantity maxenergy, then it is not
                 a valid solution. A Value of None implies that there is no
                 upper limit.

    Returns:
    boolean -- True if sensor is valid"""
    logger = logging.getLogger('fealden.unafold.validate_sensor')

    # Set reasonable default if none are specified
    if not bindingratiorange[0] or not bindingratiorange[1]:
        bindingratiorange = (.9,1.1)

    # Verify that the number of folds is within the range specified
    if numfoldrange and numfoldrange[0] and numfoldrange[1]:
        if numfoldrange[0] <= len(folds) <= numfoldrange[1]:
            logger.debug("unafold.validate_sensor(%s): GOOD -- %d folds within %d to %d" %
                         (str(sensor), len(folds), numfoldrange[0], numfoldrange[1]))
            numfoldtest = True
        else:
            logger.debug("unafold.validate_sensor(%s): BAD -- %d folds not within %d to %d" %
                         (str(sensor), len(folds), numfoldrange[0], numfoldrange[1]))
            numfoldtest = False
    else:
        logger.debug("unafold.validate_sensor(%s): NA -- num folds not specified" %
                     str(sensor))
        numfoldtest = True
        
    # Verify that the fold with the highest free energy does not exceed the
    # free energy released by the binding of the recognition by the quantity
    # maxenergy.
    #
    # Recall that energies are thermodynamic flows, thus energy out of the
    # system is negative, hence the reversal of less/more than
    highest_energy = min([fold["energy"] for fold in folds])

    if maxenergy:
        if sensor.RecognitionEnergy() + maxenergy <= highest_energy:
            logger.debug("unafold.validate_sensor(%s): GOOD -- highest fold "
                         "free energy, %f does not exceed max of %f" %
                         (str(sensor),
                          highest_energy,
                          sensor.RecognitionEnergy() + maxenergy))
            maxenergytest = True
        else:
            logger.debug("unafold.validate_sensor(%s): BAD -- highest fold "
                         "free energy,%f exceeds max of %f" %
                         (str(sensor),
                          highest_energy,
                          sensor.RecognitionEnergy() + maxenergy))
            maxenergytest = False
    else:
        logger.debug("unafold.validate_sensor(%s): NA -- highest fold free "
                     "energy not specified." %
                     (str(sensor)))
        maxenergytest = True

    # Verify that the ratio of binding_on and nonbinding_off sensors
    # is within range
    if scores["nonbinding_off"]["percent"] != 0:
        ratio = (scores["binding_on"]["percent"] /
                 scores["nonbinding_off"]["percent"])
    else:
        ratio = 0
    if(bindingratiorange[0] < ratio < bindingratiorange[1]):
        logger.debug("unafold.validate_sensor(%s): GOOD -- binding ratio"
                     "(%f vs %f) in range %f < %f < %f" %
                     (str(sensor), scores["binding_on"]["percent"],
                      scores["nonbinding_off"]["percent"],
                      bindingratiorange[0], ratio, bindingratiorange[1]))
        bindingtest = True
    else:
        logger.debug("unafold.validate_sensor(%s): BAD -- binding ratio "
                    "(%f vs %f) out of range %f < %f < %f" %
                     (str(sensor), scores["binding_on"]["percent"],
                      scores["nonbinding_off"]["percent"],
                      bindingratiorange[0], ratio, bindingratiorange[1]))
        bindingtest = False

    # Verify that the percentage of folds that the signaling behavior is
    # unknown for is less than the specified amount
    unknown = (scores["binding_unknown"]["percent"] +
               scores["nonbinding_unknown"]["percent"])
    if (unknown < maxunknownpercent):
        logger.debug("unafold.validate_sensor(%s): GOOD -- unknown percentage, %f, below max %f" %
                     (str(sensor), unknown, maxunknownpercent))
        unknowntest = True
    else:
        logger.debug("unafold.validate_sensor(%s): BAD-- unknown percentage, %f, exceeds max %f" %
                     (str(sensor), unknown, maxunknownpercent))
        unknowntest = False
        

    if(bindingtest and
       unknowntest and
       numfoldtest and
       maxenergytest):
        logger.info("unafold.validate_sensor(%s): found valid solution" %
                     (sensor))
        return True
    else:
        logger.debug("unafold.validate_sensor(%s): found invalid solution" %
                     (sensor))
        return False
