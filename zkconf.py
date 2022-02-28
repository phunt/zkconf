#!/usr/bin/env python3

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
import socket

import argparse

from zoocfg import zoocfg
from start import start
from stop import stop
from status import status
from cli import cli
from copycat import copycat
from startcat import startcat
from stopcat import stopcat
from clearcat import clearcat

usage = "usage: %prog [options] zookeeper_dir output_dir"
parser = argparse.ArgumentParser(description="ZooKeeper ensemble config generator")
parser.add_argument('zookeeper_dir', 
                    help='ZooKeeper distribution directory')
parser.add_argument('output_dir', 
                    help='Output directory of generated files')
parser.add_argument("-c", "--count", dest="count", type=int,
                  default=3, help="ensemble size (default 3)")
parser.add_argument("--servers", dest="servers",
                  default="localhost", help="explicit list of comma separated server names (alternative to --count)")
parser.add_argument("--clientportstart", dest="clientportstart", type=int,
                  default=2181, help="first client port (default 2181)")
parser.add_argument("--quorumportstart", dest="quorumportstart", type=int,
                  default=3181, help="first quorum port (default 3181)")
parser.add_argument("--electionportstart", dest="electionportstart", type=int,
                  default=4181, help="first election port (default 4181)")
parser.add_argument("--adminportstart", dest="adminportstart", type=int,
                  default=8081, help="first admin (jetty) port (default 8081)")
parser.add_argument("--weights", dest="weights",
                  default="1", help="comma separated list of weights for each server (flex quorum only, default off)")
parser.add_argument("--groups", dest="groups",
                  default="1", help="comma separated list of groups (flex quorum only, default off)")
parser.add_argument("--maxClientCnxns", dest="maxclientcnxns", type=int,
                  default=10, help="maxClientCnxns of server config (default unspecified, ZK default)")
parser.add_argument("--electionAlg", dest="electionalg", type=int,
                  default=3, help="electionAlg of server config (default unspecified, ZK default - FLE)")
parser.add_argument("--username", dest="username",
                  default="root", help="SSH username to login to servers for generating remote deployment scripts")
parser.add_argument("--trace", dest="trace", action="store_true",
                  help="Enable trace level logging to separate log file")
parser.add_argument("--ssl", dest="ssl", action="store_true",
                  help="Enable SSL support (both client-server and server-server)")
parser.add_argument("--sasl", dest="sasl", action="store_true",
                  help="Enable SASL support in client and server")
parser.add_argument("--4lwWhitelist", dest="whitelist",
                  default="", help="override the ZooKeeper default whitelist")
parser.add_argument("--4lwWhitelistAll", dest="whitelistAll", action="store_true",
                  help="whitelist all the 4lw")

options = parser.parse_args()

is_remote = False
options.clientports = []
options.quorumports = []
options.electionports = []
options.adminports = []
if options.servers != "localhost" :
    is_remote = True
    options.servers = options.servers.split(",")
    for i in range(1, len(options.servers) + 1) :
        options.clientports.append(options.clientportstart)
        options.quorumports.append(options.quorumportstart)
        options.electionports.append(options.electionportstart)
        options.adminports.append(options.adminportstart)
else :
    options.servers = []
    for i in range(options.count) :
        options.servers.append(socket.gethostname())
        options.clientports.append(options.clientportstart + i)
        options.quorumports.append(options.quorumportstart + i)
        options.electionports.append(options.electionportstart + i)
        options.adminports.append(options.adminportstart + i)

if options.weights != "1" :
    options.weights = options.weights.split(",")
else :
    options.weights = []

if options.groups != "1" :
    options.groups = options.groups.split(",")
else :
    options.groups = []

def writefile(p, content):
    f = open(p, 'w')
    f.write(content)
    f.close()

def writescript(name, content):
    p = os.path.join(options.output_dir, name)
    writefile(p, content)
    os.chmod(p, 0o755)

def copyjar(optional, srcs, jar, dstpath, dst):
    for src in srcs:
        try:
            shutil.copyfile(glob.glob(os.path.join(os.path.join(*src), jar))[0],
                            os.path.join(dstpath, dst))
            return
        except:
            pass

    if optional: return

    print("unable to find %s in %s" % (dst, options.zookeeper_dir))
    exit(1)

if __name__ == '__main__':
    os.mkdir(options.output_dir)

    serverlist = []
    for sid in range(1, len(options.servers) + 1) :
        serverlist.append([sid,
                           options.servers[sid - 1],
                           options.clientports[sid - 1],
                           options.adminports[sid - 1],
                           options.quorumports[sid - 1],
                           options.electionports[sid - 1]])

    for sid in range(1, len(options.servers) + 1) :
        serverdir = os.path.join(options.output_dir, options.servers[sid - 1] +
                                 ":" + str(options.clientports[sid - 1]))
        os.mkdir(serverdir)
        os.mkdir(os.path.join(serverdir, "data"))
        conf = zoocfg(searchList=[{'sid' : sid,
                                   'servername' : options.servers[sid - 1],
                                   'clientPort' :
                                       options.clientports[sid - 1],
                                   'adminServerPort' :
                                       options.adminports[sid - 1],
                                   'weights' : options.weights,
                                   'groups' : options.groups,
                                   'serverlist' : serverlist,
                                   'maxClientCnxns' : options.maxclientcnxns,
                                   'electionAlg' : options.electionalg,
                                   'ssl' : options.ssl,
                                   'sasl' : options.sasl,
                                   'whitelist' : options.whitelist,
                                   'whitelistAll' : options.whitelistAll}])
        writefile(os.path.join(serverdir, "zoo.cfg"), str(conf))
        writefile(os.path.join(serverdir, "data", "myid"), str(sid))

    writescript("start.sh", str(start(searchList=[{'serverlist' : serverlist, 'trace' : options.trace, 'sasl' : options.sasl}])))
    writescript("stop.sh", str(stop(searchList=[{'serverlist' : serverlist}])))
    writescript("status.sh", str(status(searchList=[{'serverlist' : serverlist}])))
    writescript("cli.sh", str(cli(searchList=[{'ssl' : options.ssl, 'sasl' : options.sasl}])))
    if is_remote:
        writescript("copycat.sh", str(copycat(searchList=[{'serverlist' : serverlist, 'username' : options.username}])))
        writescript("startcat.sh", str(startcat(searchList=[{'serverlist' : serverlist, 'username' : options.username, 'trace' : options.trace, 'sasl' : options.sasl}])))
        writescript("stopcat.sh", str(stopcat(searchList=[{'serverlist' : serverlist, 'username' : options.username}])))
        writescript("clearcat.sh", str(clearcat(searchList=[{'serverlist' : serverlist, 'username' : options.username}])))

    for f in glob.glob(os.path.join(options.zookeeper_dir, 'lib', '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, 'src', 'java', 'lib', '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, 'build', 'lib', '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, 'build', '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, 'zookeeper-server', 'target', '*.jar')):
        shutil.copy(f, options.output_dir)
    for f in glob.glob(os.path.join(options.zookeeper_dir, 'zookeeper-server', 'target', 'lib', '*.jar')):
        shutil.copy(f, options.output_dir)

    # ZK 3.8.0 added logback as the default, handle both cases...
    log4jprop_file = os.path.join(options.zookeeper_dir, "conf", "log4j.properties")
    logback_file = os.path.join(options.zookeeper_dir, "conf", "logback.xml")
    if os.path.isfile(log4jprop_file):
        shutil.copyfile(log4jprop_file, os.path.join(options.output_dir, "log4j.properties"))
    elif os.path.isfile(logback_file):
        shutil.copyfile(logback_file, os.path.join(options.output_dir, "logback.xml"))
    else:
        # Handle the case where neither file is found...
        raise Exception("Unable to find logging configuration - log4j.properties or logback.xml missing")