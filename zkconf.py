#!/usr/bin/env python

## requires use of Cheetah "sudo apt-get install python-cheetah"

import os
import shutil
import glob

from optparse import OptionParser

from zoocfg import zoocfg
from start import start
from stop import stop

usage = "usage: %prog [options] zookeeper_dir output_dir"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--count", dest="count",
                  default="3", help="ensemble size")
parser.add_option("", "--servers", dest="servers",
                  default="localhost", help="explicit list of comma separated server names (alternative to --count)")
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
parser.add_option("", "--maxClientCnxns", dest="maxclientcnxns",
                  default="10", help="maxClientCnxns of server config")
parser.add_option("", "--electionAlg", dest="electionalg",
                  default="3", help="electionAlg of server config")

(options, args) = parser.parse_args()

options.clientportstart = int(options.clientportstart)
options.quorumportstart = int(options.quorumportstart)
options.electionportstart = int(options.electionportstart)

options.clientports = []
options.quorumports = []
options.electionports = []
if options.servers != "localhost" :
    options.servers = options.servers.split(",")
    for i in xrange(1, len(options.servers) + 1) :
        options.clientports.append(options.clientportstart + 1);
        options.quorumports.append(options.quorumportstart + 1);
        options.electionports.append(options.electionportstart + 1);
else :
    options.servers = []
    for i in xrange(int(options.count)) :
        options.servers.append('localhost');
        options.clientports.append(options.clientportstart + i + 1);
        options.quorumports.append(options.quorumportstart + i + 1);
        options.electionports.append(options.electionportstart + i + 1);

if options.weights != "1" :
    options.weights = options.weights.split(",")
else :
    options.weights = []

if options.groups != "1" :
    options.groups = options.groups.split(",")
else :
    options.groups = []

options.maxclientcnxns = int(options.maxclientcnxns)
options.electionalg = int(options.electionalg)

if len(args) != 2:
    parser.error("need zookeeper_dir in order to get jars/conf, and output_dir for where to put generated")

def writefile(p, content):
    f = open(p, 'w')
    f.write(content)
    f.close()

def writescript(name, content):
    p = os.path.join(args[1], name)
    writefile(p, content)
    os.chmod(p, 0755)

if __name__ == '__main__':
    os.mkdir(args[1])

    serverlist = []
    for sid in xrange(1, len(options.servers) + 1) :
        serverlist.append([sid,
                           options.servers[sid - 1],
                           options.clientports[sid - 1],
                           options.quorumports[sid - 1],
                           options.electionports[sid - 1]])

    for sid in xrange(1, len(options.servers) + 1) :
        serverdir = os.path.join(args[1], options.servers[sid - 1] +
                                 ":" + str(options.clientports[sid - 1]))
        os.mkdir(serverdir)
        os.mkdir(os.path.join(serverdir, "data"))
        conf = zoocfg(searchList=[{'sid' : sid,
                                   'servername' : options.servers[sid - 1],
                                   'clientPort' :
                                       options.clientports[sid - 1],
                                   'weights' : options.weights,
                                   'groups' : options.groups,
                                   'serverlist' : serverlist,
                                   'maxClientCnxns' : options.maxclientcnxns,
                                   'electionAlg' : options.electionalg}])
        writefile(os.path.join(serverdir, "zoo.cfg"), str(conf))
        writefile(os.path.join(serverdir, "data", "myid"), str(sid))

    writescript("start.sh", str(start(searchList=[{'serverlist' : serverlist}])))
    writescript("stop.sh", str(stop(searchList=[{'serverlist' : serverlist}])))

    content = """#!/bin/sh
java -cp zookeeper.jar:log4j.jar:. org.apache.zookeeper.ZooKeeperMain -server "$1"\n"""
    writescript("cli.sh", content)

    content = '#!/bin/sh\n'
    for sid in xrange(1, len(options.servers) + 1) :
        content += ('echo -n "' + options.servers[sid - 1] +
                    ":" + str(options.clientports[sid - 1]) + ' "' +
                    ';echo stat | nc ' + options.servers[sid - 1] +
                    " " + str(options.clientports[sid - 1]) +
                    ' | egrep "Mode: "\n')
    writescript("status.sh", content)

    try:
        shutil.copyfile(os.path.join(args[0], "build", "lib", "log4j-1.2.15.jar"), os.path.join(args[1], "log4j.jar"))
    except:
        try:
            shutil.copyfile(os.path.join(args[0], "src", "java", "lib", "log4j-1.2.15.jar"), os.path.join(args[1], "log4j.jar"))
        except:
            print("unable to find log4j jar in %s" % (args[0]))
            exit(1)

    shutil.copyfile(os.path.join(args[0], "conf", "log4j.properties"), os.path.join(args[1], "log4j.properties"))

    try:
        jars = glob.glob(os.path.join(args[0], "build", "zookeeper-[0-9].[0-9].[0-9].jar"))
        shutil.copyfile(jars[0], os.path.join(args[1], "zookeeper.jar"))
    except:
        try:
            shutil.copyfile(os.path.join(args[0], "zookeeper-dev.jar"), os.path.join(args[1], "zookeeper.jar"))
        except:
            print("unable to find zookeeper jar in %s" % (args[0]))
            exit(1)
