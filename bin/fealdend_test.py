#!/usr/bin/env python
from fealden import searchserver, util
test_request = util.RequestElement(command="BACKTRACKING",
                                   recognition="GCATTA",
                                   output_dir="/tmp/test",
                                   email="test@example.com",
                                   maxtime=60,
                                   numfolds_lo=2,
                                   numfolds_hi=2,
                                   binding_ratio_lo=0.8,
                                   binding_ratio_hi=1.2,
                                   maxunknown_percent= .2,
                                   numsolutions=1,
                                   maxenergy=-3.4)



q = util.DirectoryQueue("/var/fealden/workqueue")
q.put(test_request)
