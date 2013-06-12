import ConfigParser
import os
import sys

class ConfigError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return repr(self.msg)


def getconfig(ini=None):
    fealden = ConfigParser.ConfigParser()
    toread = ["/etc/fealden.ini",
              "../etc/fealden.ini",
              "etc/fealden.ini",
              "fealden.ini"]
    if ini:
        toread = [ini]
    found = fealden.read(toread)

    # If no configuration is found, die
    if len(found) == 0:
        raise ConfigError("no configuration file found")

    ok = True
    errormsg = ""

    # Verify that required settings were stored in the ini
    required = ["log",
                "solutions",
                "workqueue",
                "workingdirectory",
                "pid"]

    if not fealden.has_section("Locations"):
        raise ConfigError("Locations section is missing")
    for field in required:
        if not fealden.has_option("Locations",field):
            raise ConfigError("Missing %s option" % field)

    # The following elements must be checked to verify that
    # the location referenced both exists and is writable.
    required_rw_settings = ["log",
                            "solutions",
                            "workqueue",
                            "workingdirectory"]
    
    # Check writability
    for location in [fealden.get("Locations", x) for x in required_rw_settings]:
        if not os.access(location, os.W_OK):
            errormsg += ("%s is not writable " % location)
            ok = False

    if not ok:
        raise ConfigError(errormsg)

    return fealden
