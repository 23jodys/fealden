import logging
import pickle
import os
import sys
import argparse

from nose.tools import nottest

from fealden import unafold
from fealden import util


def test_combine_stems_generator():
    def _combine_stems(left_stems, right_stems, expected, seq_length, message):
        result = unafold.combine_stems(left_stems, right_stems, seq_length, 0, True)
        print ("Test case: %s, Expected %s, Result %s" %
               (message, expected, result))
        assert result == expected

    tests = [
        [
            [
                { "lh":{"start":2, "end":9}, "rh":{"start":22,"end":29} },
                { "lh":{"start":10, "end":11}, "rh":{"start":18,"end":19} },
                { "lh":{"start":31, "end":38}, "rh":{"start":51,"end":58} },
                { "lh":{"start":40, "end":41}, "rh":{"start":47,"end":48} }
            ],
            [
                { "lh":{"start":2, "end":11}, "rh":{"start":18,"end":29} },
                { "lh":{"start":31, "end":41}, "rh":{"start":47,"end":58} }
            ],
            58,
            "Basic test"
        ],
        [
            [
                {"lh":{"start":1, "end":4}, "rh":{"start":9, "end":12}},
                {"lh":{"start":14, "end":17}, "rh":{"start":23, "end":26}}
            ],
            [
                {"lh":{"start":1, "end":4}, "rh":{"start":9, "end":12}},
                {"lh":{"start":14, "end":17}, "rh":{"start":23, "end":26}}
            ],
            26,
            "Basic test"
        ],
        [
            [
                {"lh":{"start":10, "end":21}, "rh":{"start":39, "end":50}},
                {"lh":{"start":22, "end":23}, "rh":{"start":29, "end":30}}
            ],
            [
                {"lh":{"start":10, "end":23}, "rh":{"start":29, "end":50}}
            ],
            58,
            "Basic test"
        ],
        [
            [
                {'rh': {'start': 22, 'end': 29}, 'lh': {'start': 2, 'end': 9}},
                {'rh': {'start': 18, 'end': 19}, 'lh': {'start': 10, 'end': 11}},
                {'rh': {'start': 51, 'end': 58}, 'lh': {'start': 31, 'end': 38}},
                {'rh': {'start': 47, 'end': 48}, 'lh': {'start': 40, 'end': 41}}
            ],
            [
                {'rh': {'start': 18, 'end': 29}, 'lh': {'start': 2, 'end': 11}},
                {'rh': {'start': 47, 'end': 58}, 'lh': {'start': 31, 'end':41}}
            ],
            58,
            "Two bulge loops"
        ]

    ]


    for test in tests:
        yield _combine_stems, [test[0][0]], test[0][1:], test[1], test[2], test[3]

def test_fluorophore_distance_generator():

    def _fluorophore_distance(stem1, expected, message):
        result = unafold.fluorophore_distance(stem1)
        print "_fluorophore_distance(%s)" % stem1
        assert result == expected, ("Test case: %s, Expected %s, Result %s " %
                                    (message, expected, result))
        
    tests = [
        [{"lh":{"start":4,"end":15}, "rh":{"start":21, "end":32}}, 2, "f in the tail"],
        [{"lh":{"start":7,"end":15}, "rh":{"start":24, "end":32}},5, "f in the tail"],
        [{"lh":{"start":1,"end":4}, "rh":{"start":9, "end":12}},0, "f @ the base of stem"],
        [{"lh":{"start":2,"end":4}, "rh":{"start":10, "end":12}},0, "f @ adjacent to base of stem"]
        ]

    for test in tests:
        yield _fluorophore_distance, test[0], test[1], test[2]
    
def test_quench_distance_generator():
    """quench_distance"""

    def _quencher_distance(stem1, stem2, quencher, expected, message):
        result = unafold.quencher_distance(stem1, stem2, quencher)

            
        if result != expected:
            print "_quencher_distance(%s, %s, %s)" % (stem1,stem2,quencher)
            assert False, ("Test case: %s, expected: %s, Result: %s" %
                           (message,
                            expected,
                            result))

    tests = [
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 5, 0, 'q @ stem1 lh side base'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 7, 2, 'q @ stem1 lh side middle'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 10, 5, 'q @ stem1 lh side top'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 19, 0, 'q @ stem1 rh side base'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 16, 3, 'q @ stem1 rh side middle'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39},
          'lh': {'start': 24, 'end': 29}}, 14, 5, 'q @ stem1 rh side top'],
        [{'rh': {'start': 14, 'end': 19}, 'lh': {'start': 5, 'end': 10}},
         {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}},
         24, 5, 'q @ stem2 lh side base'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 27, 8, 'q @ stem2 lh side middle'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 29, 10, 'q @ stem2 lh side top'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 39, 5, 'q @ stem2 rh side base'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 36, 8, 'q @ stem2 rh side middle'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 34, 10, 'q @ stem2 rh side top'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 13, 100, 'q @ hairpin loop'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 23, 4, 'q @ middle loop'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 4, -1, 'q @ tail'],
        [{'rh': {'start': 14, 'end': 19},
          'lh': {'start': 5, 'end': 10}}, {'rh': {'start': 34, 'end': 39}, 'lh': {'start': 24, 'end': 29}}, 2, -3, 'q @ tail']]
    


    for test in tests:
        yield _quencher_distance, test[0], test[1], test[2], test[3], test[4]


def test_fold_type_generator():
    """fold_type()"""
    test_foldings = os.listdir("test/tests/fold_type/")

    def _fold_type(fold, recognition, quencher, expected, foldnum, comment):
        result = unafold.fold_type(fold, recognition, quencher, True)
        print("_fold_type(): Examining %s, recognition %s and "
              "foldnum %s" %
              (''.join([ x["nucl"] for x in fold["seq"]]),
               ''.join(recognition),
               foldnum))

        if result == expected:
            assert True
        else:
            assert False, ("Test case: %s, Expected: %s, Result: %s" %
                           (comment,
                            expected,
                            result))

    for testname in test_foldings:
        print "testing %s" % testname
        test_file = open("test/tests/fold_type/" + testname)
        test = pickle.load(test_file)
        test_file.close()

        yield _fold_type, test[0], test[1], test[2], test[3], test[4], test[5]

def fold_type_make_case(foldnum, seq, folding, recognition, quencher, expected, comment):
    tosave = open(os.path.join("tests/fold_type/", seq + "_" + foldnum), 'w')
    pickle.dump([folding, list(recognition), quencher, expected, foldnum, comment], tosave)
    tosave.close()
    print [folding, list(recognition), quencher, expected, foldnum, comment]

def test_check_recognition_stem_generator():
    tests = [
        [[],[],[],0.0,  "both empty"],  
        [[],[],list('AAGGA'), 0.0, "empty stem"],
        [list('AAGGA'), list('AAGGA')[::-1], [], 0.0, "empty recognition"],
        [list('AAGGA'), [], list('AAGGA'), 1.0, "perfect match"],
        [list('ATTA'), [],list('ATGC'), 1/2.0, "half match"],
        [list('AATATA'), [],list('AAGCGC') , 1/3.0, "1/3 match"],
        [list('AATTAA'), [],list('GCTTGC') , 1/3.0, "1/3 match"],
        [list('GCT'), list('AGC'), list('AGC'), 1.0, "full match in rh stem"],
        [list('CCC'), list('GGG'), list('ATA'), 0.0, "no match"],
        [list('GCGC'), [],list('GGGGGGGGGGG'), 1/11.0, "recognition longer than stem"],
        [list('GCGCCGCCGCCG'),[], list('GCCG'), 1.0, "full recognition in longer stem"],
        [list('CC'), [],list('CCC'), 2.0/3.0, "found problem"],
        [list('GGACGATAT'), list('GTATCGCC'), list('CGATA'), 1.0, "uneven lh rh stems"]
        ]

    def _check_recognition_stem(stemlh, stemrh, recognition, expected, errmsg):
        if unafold.check_recognition_stem(stemlh, stemrh, recognition) == expected:
            assert True
        else:
            print("%s, expected %f, found %f" %
                  (errmsg,
                   expected,
                   verify.check_recognition_stem(stemlh, stemrh, recognition, True)))
            assert False

    for test in tests:
        yield _check_recognition_stem, test[0], test[1], test[2], test[3], test[4]



def run_hybrid_ss_min_test_generator():
    """Reads in all the tests cases in tests/run_hybrid_ss_min and
       checks that each is parsed correctly by run_hybrid_ss_min()"""

    def _run_hybrid_ss_min(seq, expected):
        results = unafold.run_hybrid_ss_min(seq, True)
        assert results == expected

    test_seqs = os.listdir("test/tests/run_hybrid_ss_min")
    
    for test in test_seqs:
        try:
            print "test/tests/run_hybrid_ss_min/" + test
            expected_file = open("test/tests/run_hybrid_ss_min/" + test)
            expected = pickle.load(expected_file)
            expected_file.close()
        except:
            print "Could not open file"
            assert False

        yield _run_hybrid_ss_min, test, expected

def run_hybrid_ss_min_make_case(seq):
    """given a sequence string, pickle the output to
    tests/run_hybrid_ss_min"""

    test_file = "tests/run_hybrid_ss_min/" + seq

    tosave = open(test_file, 'w')
    pickle.dump(unafold.run_hybrid_ss_min(seq), tosave)
    tosave.close()

def test_find_stems_generator():
    def _find_stems(folding, expected):
        results = unafold.find_stems(folding, True)
        print("find_stems(): found %d stems" % ( len(results)))
        if results != expected:
            print("unafold_find_stems_test(): stems, expected %s, found %s" %
                  ( expected, str(results)))
            print "unafold_find_stems_test(): pretty printed sequence"
            print unafold.format_fold_debug(folding)
            assert False
        else:
            pass

    test_foldings = os.listdir("test/tests/find_stems/")

    for test in test_foldings:
        try:
            expected_file = open("test/tests/find_stems/" + test)
            expected = pickle.load(expected_file)
            expected_file.close()
        except IOError:
            sys.stderr.write("test_find_stems_generator(): could not open file %s" % "test/tests/find_stems/" + test)
            assert False

        yield _find_stems, expected[0], expected[1]
            

def find_stems_make_case(seq, foldnum, comment):
    foldings = unafold.parse_ct(unafold.run_hybrid_ss_min(seq))

    tosave_filename = "tests/find_stems/" + seq + "_%d" % (foldnum - 1)
    tosave = open(tosave_filename,'w')
    test_case = [foldings[foldnum - 1],unafold.find_stems(foldings[foldnum - 1]), comment]
    pickle.dump(test_case, tosave)
    print("find_stems_make_case(%s, %d, %s): pickling %s" %
          (seq, foldnum, comment, test_case))
    tosave.close()


@nottest
def score_sensor_test_generator():
    def _run_score_sensor(sensor, folds, expected_scores):
        scores = unafold.score_sensor(sensor, folds)

        print("_score_sensor_test(%s): expected %s, got %s" %
              (sensor, expected_scores, scores))
        assert scores == expected_scores

    test_foldings = os.listdir("test/tests/score_sensor/")

    for test in test_foldings:
        try:
            expected_file = open("test/tests/score_sensor/" + test)
            expected = pickle.load(expected_file)
            expected_file.close()
        except IOError:
            sys.stderr.write("score_sensor_test_generator(): could not open file %s" % "test/tests/score_sensor/" + test)
            assert False

        yield _run_score_sensor, expected[0], expected[1], expected[2]

def score_sensor_make_case(sensor):
    folds = unafold.parse_ct(unafold.run_hybrid_ss_min(sensor, True))
    scores = unafold.score_sensor(sensor, folds)

    tosave_filename = "tests/score_sensor/" + str(sensor)
    tosave = open(tosave_filename,'w')

    pickle.dump((sensor, folds, scores), tosave)

    print("score_sensor_make_case(%s): pickling %s" %
          (sensor, (folds, scores)))
    tosave.close()



def validate_sensor_test_generator():
    def _run_validate_sensor(sensor, scores, folds,
                             bindingratiorange,
                             maxunknownpercent,
                             numfoldrange, maxenergy, expected):

        results = unafold.validate_sensor(sensor, scores, folds,
                                          bindingratiorange,
                                          maxunknownpercent,
                                          numfoldrange, maxenergy)

        print("_run_validate_sensor(%s, %s): called with " %
              (sensor, bindingratiorange))
        if maxunknownpercent:
            print("       maxunknownpercent: %f" % maxunknownpercent)
        if numfoldrange:
            print("       numfoldrange: %d to %d" % (numfoldrange[0], numfoldrange[1]))
        if maxenergy:
            print("       maxenergy: %f" % maxenergy)
               
        assert results == expected

    test_seqs = os.listdir("test/tests/validate_sensor/")
    
    for test in test_seqs:
        try:
            print "test/tests/validate_sensor/" + test
            expected_file = open("test/tests/validate_sensor/" + test)
            expected = pickle.load(expected_file)
            expected_file.close()
        except:
            print "Could not open file"
            assert False

        #pickle.dump((sensor, scores, folds, test[3],test[4],test[5],test[6],test[7]), tosave)

        yield (_run_validate_sensor, expected[0], expected[1], expected[2],
               expected[3],expected[4], expected[5], expected[6], expected[7])
        

def validate_sensor_make_cases():
    # [ Recog, Stem1, Stem2, binding_ratio, maxunknownpercent, numfoldrange, maxenergy, expected ]
    tests = [["ATTA","CGA","TCC",(.9,1.1),.2,(2,4),-1.3,False],
             ["ATTA","CCC","CGC",(.9,1.1),.2,(2,4),-10,False],
             ["ATTA","CCC","CGC",(.6,.7),.2,(2,4),None,True],
             ["ATTA","GCG","CCC",(.9,1.1),.2,None,None,False],
             ["ATTA","TCA","CC",(.2,.8),.2,None,0,True],
             ["ATTAGC","TCCA","CCCC",(.9,1.1),.2,None,None,False]]

    for test in tests:
        sensor = util.Sensor(test[0])
        sensor.SetStem1(test[1])
        sensor.SetStem2(test[2])

        test_file = "tests/validate_sensor/" + str(sensor)
        tosave = open(test_file, 'w')

        folds = unafold.parse_ct(unafold.run_hybrid_ss_min(sensor))
        scores = unafold.score_sensor(sensor,folds)

        pickle.dump((sensor, scores, folds, test[3],test[4],test[5],test[6],test[7]), tosave)
        print("validate_sensor_make_cases(): storing folds and scores for %s" % str(sensor))
        tosave.close()


def process_command_line(argv):
    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Verify that DNA sequence(s) from stdin make the right structures')

    # define options here:
    parser.add_argument('-r', action="store_true", dest="run_hybrid_ss_min",
                        default=False,
                        help="Read STDIN and write test cases for run_hybrid_ss_min")

    parser.add_argument('-f', action="store_true", dest="find_stems",
                        default=False,
                        help="Read STDIN and write test cases for find_stems()")

    parser.add_argument('-b', action="store_true", dest="binding", default=False)
    parser.add_argument('-s', action="store_true", dest="score_sensor", default=False)
    parser.add_argument('-v', action="store_true", dest="validate_sensor", default=False)
    args = parser.parse_args(argv)
    return args


def main():
    args = process_command_line(sys.argv[1:])

    if args.validate_sensor:
        validate_sensor_make_cases()
        return True
    
    for line in sys.stdin:
        line = line.strip()
        sys.stderr.write("Processing case %s\n" % line)
        if args.binding:
            # Assumes that run_hybrid_ss_min produces valid
            # foldings
            # Takes a CSV file with the following format
            # Recognition, Generated Sequence, quencher, fold number, type, comment
            #
            # Where fold number is is the 1 based index as returned
            # from UNAfold, and type binding_on/nonbinding_off/badbind/badnonbind
            elements = line.split(',')

            foldings = unafold.parse_ct(unafold.run_hybrid_ss_min(elements[1]))

            try:
                comment = elements[5]
            except IndexError:
                comment = ""

            fold_type_make_case(elements[3],
                                elements[1],
                                foldings[int(elements[3]) - 1],
                                elements[0],
                                int(elements[2]),
                                elements[4],
                                comment)

        if args.score_sensor:
            elements = line.split(',')

            sensor = util.Sensor(elements[0])
            sensor.SetStem1(elements[1])
            sensor.SetStem2(elements[2])
            score_sensor_make_case(sensor)

        if args.run_hybrid_ss_min:
            run_hybrid_ss_min_make_case(line)

        if args.find_stems:
            # Reads in STDIN to make regression test cases to test find_stems()
            # Assumes that run_hybrid_ss_min() and parse_ct() are working correctly
            # File format
            #
            # sequence, foldnum, comment

            elements = line.split(',')
            
            try:
                comment = elements[2]
            except IndexError:
                comment = ""
            
            find_stems_make_case(elements[0], int(elements[1]), comment)

if __name__ == '__main__':
    main()

    sys.exit(0)


