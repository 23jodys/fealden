from glob import glob
import itertools
import os
import pickle
from nose.tools import nottest

from fealden import distance

def test_generator():
    def _execute(function, fold, expected):
        result = function(fold)
        print "Expected: {}".format(expected)
        print "Got     : {}".format(result)
        assert result == expected

    test_inputs = glob("test/gengraph/*.parse_ct")
    test_gengraph_outputs = glob("test/gengraph/*.gengraph")
    test_find_shortest_path_outputs = glob("test/gengraph/*.find_shortest_path")
    if len(test_gengraph_outputs + test_find_shortest_path_outputs) == 0:
        # The outputs of this test are long-winded,
        # if necessary the outputs can be regenerated from the 
        # functions under test, so use wisely!
        # The inputs are static and match the output of parse_ct which 
        # shouldn't be changing anytime soon
        for test in test_inputs:
            (testname, testext) = os.path.splitext(test)
            with open("test/gengraph/" + test) as parsefile:
                parsed = pickle.load(parse_file)
                # Generate the graph test outputs
                with open("test/gengraph/{}.gengraph".format(testname), w) as f:
                    case = distance.gengraph(parsed)
                    pickle.store(case)
                with open("test/gengraph/{}.find_shortest_path".format(testname), w) as f:
                    pathcase = distance.find_shortest_path(case)
                    pickle.store(pathcase)

    for (function, test) in itertools.product([distance.gen_graph, distance.find_shortest_path], test_inputs):
        try:
            expected_file = open("test/gengraph/" + test)
            expected = pickle.load(expected_file)
            expected_file.close()
        except IOError:
            sys.stderr.write("gengraph2_test_generator(): could not open file %s" % "test/gengraph/" + test)
            assert False

        yield _gengraph_execute, expected[0]["seq"], expected[1]
            
@nottest
def gengraph_test_generator():
    def _gengraph_execute(fold, expected, message):
        result = distance.gengraph(fold)
        print "Testing {}".format(message)
        print "Expected: {}".format(expected)
        print "Got     : {}".format(result)
        assert result == expected

    def _test_parser(testline):
        testinput = []
        for el in testline.split(","):
            print el
            (member, length) = el.split(":")
            member_data = member.split(" ")
            if len(member_data) == 2:
                testinput += [{"member_type": member_data[0],
                               "member_index": member_data[1],
                               "member_side": ""}
                               for i in range(int(length))]
            else:
                testinput += [{"member_type": member_data[0],
                               "member_index": member_data[1], 
                               "member_side": member_data[2]}
                               for i in range(int(length))]
        print testinput
        return testinput


    tests = (
                ("Tail 1:5,Stem 1 l:4,Loop 1:5,Stem 1 r:4,Tail 2:3",
                {},
                "Simple one stem test"),
                ("Tail 1:5,Stem 1 l:8,Loop 1:6,Stem 1 r:8,Loop 2:3,Stem 2 l:6,Loop 3:3,Stem 3 l:7,Loop 4:5,Stem 3 r:7,Loop 5:4,Stem 2 r:6,Tail 2:2",
                {},
                "More complicated three stem with bridge loop")
            )

    for test in tests:
        yield _gengraph_execute, _test_parser(test[0]), test[1], test[2] 

@nottest
def lineardistance_test_generator():
	def _lineardistance_execute(stems, loops, tails, nucl1, nucl2, expected, message):
		result = distance.lineardistance(stems, loops, tails, nucl1, nucl2)
		print "Testing {}".format(message)
		print "Expected: {}".format(expected)
		print "Got:      {}".format(result)
		assert result == expected

	tests = [
			[
				[{'lh':(5,6,7,8,9), 'rh':(16,17,18,19,20)}], 
				(10,11,12,13,14,15), 
				((1,2,3,4), (21,22,23,24,25)),
				"Single Stem: ",
				(	
					(1, 12, 4, "in loop, in tail"),
					(5,20,2, "binding pair")
				) 
			]	
		]
	
	for test in tests:
		for subtest in test[4]:
			yield _lineardistance_execute, test[0], test[1], test[2], subtest[0], subtest[1], subtest[2], test[3] + subtest[3]

