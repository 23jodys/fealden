from fealden.lib import unafold, util, unafold_three_stem

def test_fold_type_generator():
    expected = ["binding_on", "nonbinding_off"]
        
    sensor = util.Sensor("ATTA")
    sensor.SetStem1("CCC")
    sensor.SetStem2("ATG")
    
    folds = unafold.parse_ct(unafold.run_hybrid_ss_min(sensor))
    print "expected %d folds, got %d" %(len(expected), len(folds))
    assert len(folds) == len(expected)
    i = 0
    for fold in folds:
        result = unafold_three_stem.fold_type(sensor, "ATTA", 12)
        print "expected %s, but got %s" % ( expected[i], result)
        if result != expected[i]:
            failure = True
        i += 1
                                                                        
    assert failure != True
