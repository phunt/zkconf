#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

## requires use of Cheetah "sudo apt-get install python-cheetah"

import os
import shutil
import glob

from optparse import OptionParser

from zoocfg import zoocfg
from start import start
from stop import stop
from status import status

usage = "usage: %prog [options] zookeeper_dir output_dir"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--count", dest="count", type="int",
                  default=3, help="ensemble size (default 3)")
parser.add_option("", "--servers", dest="servers",
                  default="localhost", help="explicit list of comma separated server names (alternative to --count)")
parser.add_option("", "--clientportstart", dest="clientportstart", type="int",
                  default=2181, help="first client port (default 2181)")
parser.add_option("", "--quorumportstart", dest="quorumportstart", type="int",
                  default=3181, help="first quorum port (default 3181)")
parser.add_option("", "--electionportstart", dest="electionportstart", type="int",
                  default=4181, help="first election port (default 4181)")
parser.add_option("", "--weights", dest="weights",
                  default="1", help="comma separated list of weights for each server (flex quorum only, default off)")
parser.add_option("", "--groups", dest="groups",
                  default="1", help="comma separated list of groups (flex quorum only, default off)")
parser.add_option("", "--maxClientCnxns", dest="maxclientcnxns", type='int',
                  default=10, help="maxClientCnxns of server config (default unspecified, ZK default)")
parser.add_option("", "--electionAlg", dest="electionalg", type='int',
                  default=3, help="electionAlg of server config (default unspecified, ZK default - FLE)")

(options, args) = parser.parse_args()

options.clientports = []
options.quorumports = []
options.electionports = []
if options.servers != "localhost" :
    options.servers = options.servers.split(",")
    for i in xrange(1, len(options.servers) + 1) :
        options.clientports.append(options.clientportstart);
        options.quorumports.append(options.quorumportstart);
        options.electionports.append(options.electionportstart);
else :
    options.servers = []
    for i in xrange(options.count) :
        options.servers.append('localhost');
        options.clientports.append(options.clientportstart + i);
        options.quorumports.append(options.quorumportstart + i);
        options.electionports.append(options.electionportstart + i);

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

def writefile(p, content):
    f = open(p, 'w')
    f.write(content)
    f.close()

def writescript(name, content):
    p = os.path.join(args[1], name)
    writefile(p, content)
    os.chmod(p, 0755)

def copyjar(optional, srcs, jar, dstpath, dst):
    for src in srcs:
        try:
            shutil.copyfile(glob.glob(os.path.join(os.path.join(*src), jar))[0],
                            os.path.join(dstpath, dst))
            return
        except:
            pass

    if optional: return

    print("unable to find %s in %s" % (dst, args[0]))
    exit(1)

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
    writescript("status.sh", str(status(searchList=[{'serverlist' : serverlist}])))

    content = """#!/bin/bash
java -cp ./*:. org.apache.zookeeper.ZooKeeperMain -server "$1"\n"""
    writescript("cli.sh", content)

    for f in glob.glob(os.path.join(args[0], 'lib', '*.jar')):
        shutil.copy(f, args[1])
    for f in glob.glob(os.path.join(args[0], 'src', 'java', 'lib', '*.jar')):
        shutil.copy(f, args[1])
    for f in glob.glob(os.path.join(args[0], 'build', 'lib', '*.jar')):
        shutil.copy(f, args[1])
    for f in glob.glob(os.path.join(args[0], '*.jar')):
        shutil.copy(f, args[1])
    for f in glob.glob(os.path.join(args[0], 'build', '*.jar')):
        shutil.copy(f, args[1])

    shutil.copyfile(os.path.join(args[0], "conf", "log4j.properties"), os.path.join(args[1], "log4j.properties"))
