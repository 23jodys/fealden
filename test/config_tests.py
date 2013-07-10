import ConfigParser
from fealden import config
import io
import os
import shutil
import tempfile

def config_test():
    test_configs = ([
"""
[Locations]
log: asdf
solutions: asdf
workqueue: asdf
pid: asdf
""",
        False, "Missing workingdirectory"],
                    ["", False, "Empty config"],
                    [
"""
[Locations]
log: /asfd
workingdirectory: /asdf
solutions: /asdf
workqueue: /asdf
pid: /asdf
""",
                        False, "files don't exist"],
                    )
                    
    for test in test_configs:
        testdir = tempfile.mkdtemp()
        testini = os.path.join(testdir, "fealden.ini")
        with open(testini, "w") as f:
            f.write(test[0])

        try:
            fealden = config.getconfig(testini)
        except config.ConfigError as e:
            if test[1]:
                print "BAD - Test: %s, received %s" % (test[2], e.msg)
                assert False
            else:
                assert True
        else:
            if test[1]:
                assert True
            else:
                print "BAD - Test %s: Expected ConfigError, but received none" % test[2]
                assert False
        finally:
            shutil.rmtree(testdir)
    
