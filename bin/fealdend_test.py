#!/usr/bin/env python
import logging
import time
from fealden import searchserver, util
logger = logging.getLogger("fealden")
logger.setLevel(logging.DEBUG)
test_requests = [ util.RequestElement(command="BACKTRACKING",
                                      recognition="ATTA",
                                      output_dir="/var/fealden/solutions/ATTA",
                                      email="test@example.com",
                                      maxtime=2),
                  util.RequestElement(command="BACKTRACKING",
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
                                      maxenergy=-3.4)]
q = util.DirectoryQueue("/var/fealden/workqueue")
#for i in test_requests:
#    q.put(i)
#    time.sleep(10)
q.put(test_requests[0])
