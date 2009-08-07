#!/usr/bin/env python

## requires use of Cheetah "sudo apt-get install python-cheetah"

import os
import shutil
from optparse import OptionParser

from zoocfg import zoocfg
from start import start
from stop import stop

usage = "usage: %prog [options] zookeeper_trunk_dir"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--count", dest="count",
                  default="3", help="ensemble size")
parser.add_option("", "--clientportstart", dest="clientportstart",
                  default="2180", help="first client port")
parser.add_option("", "--quorumportstart", dest="quorumportstart",
                  default="3180", help="first quorum port")
parser.add_option("", "--electionportstart", dest="electionportstart",
                  default="4180", help="first election port")
parser.add_option("", "--weights", dest="weights",
                  default="1", help="comma separated list of weights for each server (flex quorum only)")
parser.add_option("", "--groups", dest="groups",
                  default="1", help="comma separated list of groups (flex quorum only)")

(options, args) = parser.parse_args()

options.count = int(options.count)
options.clientportstart = int(options.clientportstart)
options.quorumportstart = int(options.quorumportstart)
options.electionportstart = int(options.electionportstart)

if options.weights != "1" :
    options.weights = options.weights.split(",")
else :
    options.weights = []

if options.groups != "1" :
    options.groups = options.groups.split(",")
else :
    options.groups = []

if len(args) != 1:
    parser.error("need zookeeper_trunk_dir in order to get jars and conf")

if __name__ == '__main__':
    serverlist = []
    for sid in xrange(1, options.count + 1) :
        serverlist.append([sid,
                           options.clientportstart + sid,
                           options.quorumportstart + sid,
                           options.electionportstart + sid])

    for sid in xrange(1, options.count + 1) :
        serverdir = "s" + str(sid)
        os.mkdir(serverdir)
        os.mkdir(os.path.join(serverdir, "data"))
        conf = zoocfg(searchList=[{'sid' : sid,
                                   'clientPort' :
                                       options.clientportstart + sid,
                                   'weights' : options.weights,
                                   'groups' : options.groups,
                                   'serverlist' : serverlist}])
        f = open(os.path.join(serverdir, "zoo.cfg"), 'w')
        f.write(str(conf))
        f.close()
        f = open(os.path.join(serverdir, "data", "myid"), 'w')
        f.write(str(sid))
        f.close()

    f = open("start.sh", 'w')
    f.write(str(start(searchList=[{'serverlist' : serverlist}])))
    f.close()
    os.chmod("start.sh", 0755)

    f = open("stop.sh", 'w')
    f.write(str(stop(searchList=[{'serverlist' : serverlist}])))
    f.close()
    os.chmod("stop.sh", 0755)

    shutil.copyfile(os.path.join(args[0], "src", "java", "lib", "log4j-1.2.15.jar"), "log4j.jar")
    shutil.copyfile(os.path.join(args[0], "conf", "log4j.properties"), "log4j.properties")
    shutil.copyfile(os.path.join(args[0], "zookeeper-dev.jar"), "zookeeper.jar")

    f = open("cli.sh", 'w')
    f.write('java -cp zookeeper.jar:log4j.jar:. org.apache.zookeeper.ZooKeeperMain -server $1')
    f.close()
    os.chmod("cli.sh", 0755)
