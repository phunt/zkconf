#!/usr/bin/env python

## requires use of Cheetah "sudo apt-get install python-cheetah"

import os
import shutil
from optparse import OptionParser

from zoocfg import zoocfg
from start import start
from stop import stop

usage = "usage: %prog [options] zookeeper_dir output_dir"
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

if len(args) != 2:
    parser.error("need zookeeper_dir in order to get jars/conf, and output_dir for where to put generated")

if __name__ == '__main__':
    os.mkdir(args[1])

    serverlist = []
    for sid in xrange(1, options.count + 1) :
        serverlist.append([sid,
                           options.clientportstart + sid,
                           options.quorumportstart + sid,
                           options.electionportstart + sid])

    for sid in xrange(1, options.count + 1) :
        serverdir = os.path.join(args[1], "s" + str(sid))
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

    startcmd = os.path.join(args[1], "start.sh")
    f = open(startcmd, 'w')
    f.write(str(start(searchList=[{'serverlist' : serverlist}])))
    f.close()
    os.chmod(startcmd, 0755)

    stopcmd = os.path.join(args[1], "stop.sh")
    f = open(stopcmd, 'w')
    f.write(str(stop(searchList=[{'serverlist' : serverlist}])))
    f.close()
    os.chmod(stopcmd, 0755)

    shutil.copyfile(os.path.join(args[0], "src", "java", "lib", "log4j-1.2.15.jar"), os.path.join(args[1], "log4j.jar"))
    shutil.copyfile(os.path.join(args[0], "conf", "log4j.properties"), os.path.join(args[1], "log4j.properties"))
    shutil.copyfile(os.path.join(args[0], "zookeeper-dev.jar"), os.path.join(args[1], "zookeeper.jar"))

    clicmd = os.path.join(args[1], "cli.sh")
    f = open(clicmd, 'w')
    f.write('java -cp zookeeper.jar:log4j.jar:. org.apache.zookeeper.ZooKeeperMain -server $1')
    f.close()
    os.chmod(clicmd, 0755)
