# Generate configuration for Apache ZooKeeper ensemble

**Author: [Patrick Hunt](https://people.apache.org/~phunt/)** (follow me on [twitter](https://twitter.com/phunt))

## Summary

[This project](https://github.com/phunt/zkconf) will generate all of the configuration needed to run a [ZooKeeper ensemble](https://zookeeper.apache.org) I mainly use this tool for localhost based testing, but it can generate configurations for any list of servers (see the --server option).

### What is Apache ZooKeeper

From the [official site](https://zookeeper.apache.org) "ZooKeeper is a high-performance coordination service for distributed applications."

It exposes common services - such as naming, configuration management, synchronization, and group services - in a simple interface so you don't have to write them from scratch. You can use it off-the-shelf to implement consensus, group management, leader election, and presence protocols. And you can build on it for your own, specific needs.

## License

This project is licensed under the Apache License Version 2.0

## Requirements

- Python 2 and 3 are supported.
- Cheetah - see below

### Requirements - Cheetah Python 2

- [Cheetah](http://www.cheetahtemplate.org) templating package are necessary to run this
  \*\* On ubuntu "sudo apt-get install python-cheetah" or "pip install cheetah"

before using the first time (or on update) run the following command

```bash
cheetah compile \*.tmpl
```

### Requirements - Cheetah Python 3

- Cheetah has been forked to support python 3 - "pip install cheetah3"

before using the first time (or on update) run the following command

```bash
cheetah compile \*.tmpl # you may need to prefix with "python3" if not the default
```

## Usage

<pre>
usage: zkconf.py [-h] [-c COUNT] [--servers SERVERS]
                 [--clientportstart CLIENTPORTSTART]
                 [--quorumportstart QUORUMPORTSTART]
                 [--electionportstart ELECTIONPORTSTART]
                 [--adminportstart ADMINPORTSTART] [--weights WEIGHTS]
                 [--groups GROUPS] [--maxClientCnxns MAXCLIENTCNXNS]
                 [--electionAlg ELECTIONALG] [--username USERNAME] [--trace]
                 [--ssl] [--sasl] [--4lwWhitelist WHITELIST]
                 [--4lwWhitelistAll]
                 zookeeper_dir output_dir

ZooKeeper ensemble config generator

positional arguments:
  zookeeper_dir         ZooKeeper distribution directory
  output_dir            Output directory of generated files

optional arguments:
  -h, --help            show this help message and exit
  -c COUNT, --count COUNT
                        ensemble size (default 3)
  --servers SERVERS     explicit list of comma separated server names
                        (alternative to --count)
  --clientportstart CLIENTPORTSTART
                        first client port (default 2181)
  --quorumportstart QUORUMPORTSTART
                        first quorum port (default 3181)
  --electionportstart ELECTIONPORTSTART
                        first election port (default 4181)
  --adminportstart ADMINPORTSTART
                        first admin (jetty) port (default 8081)
  --weights WEIGHTS     comma separated list of weights for each server (flex
                        quorum only, default off)
  --groups GROUPS       comma separated list of groups (flex quorum only,
                        default off)
  --maxClientCnxns MAXCLIENTCNXNS
                        maxClientCnxns of server config (default unspecified,
                        ZK default)
  --electionAlg ELECTIONALG
                        electionAlg of server config (default unspecified, ZK
                        default - FLE)
  --username USERNAME   SSH username to login to servers for generating remote
                        deployment scripts
  --trace               Enable trace level logging to separate log file
  --ssl                 Enable SSL support (both client-server and server-
                        server)
  --sasl                Enable SASL support in client and server
  --4lwWhitelist WHITELIST
                        override the ZooKeeper default whitelist
  --4lwWhitelistAll     whitelist all the 4lw
</pre>

Where zookeeper_dir is the location of your ZooKeeper trunk (zkconf copies the jars/confs from this directory into the output_dir to make your life easier). And output_dir is the directory to which we will output the generated files (assumption is that this is a non-existent directory - ie zkconf will create it)

example of typical use; 9 server quorum:

```bash
zkconf.py --count 9 ~/zookeeper_trunk test9servers
```

```bash
zkconf.py --servers "host1.com,host2.com,168.1.1.1" ~/zookeeper_trunk test3servers
```

example of using weights/groups (only for flex quorum, not typical); 9 servers with 3 groups

```bash
zkconf.py -c 9 --weights="1,1,1,1,1,0,0,0,0" --groups="1:2:3:4:5,6:7,8:9" ~/dev/workspace/gitzk testflexquroum
```

Running localhost (default) starts client:quorum:election ports as 2181:3181:4181 respectively. Running non-localhost (--servers) starts client:quorum:elections ports for all hosts as 2181:3181:4181.

- cli.sh "server:port,server:port,..." - open a client to the server list
- status.sh - status of each of the servers (prints leader | follower if active)
- start.sh - start the ensemble (logs are output to the respective server subdir, localhost only)
- stop.sh - stop the ensemble (localhost only)

## Running remotely

If servers are listed in the command line, zkconf will generate shell scripts which help you to upload ZooKeeper files and start/stop ensemble remotely. For instance, you want to start a "real" ensemble running on separate machines / VMs.

```bash
zkconf.py --servers "host1.com,host2.com,168.1.1.1" --username foobar ~/zookeeper_trunk test3servers
```

Argument username is optional, root will be used by default if it's missing. The following scripts will be available:

- copycat.sh - transfer the files to remote servers
- startcat.sh - start ensemble remotely
- stopcat.sh - stop ensemble remotely

Status can be checked with the same script that was mentioned in the previous section.

## SSL

SSL support can be enabled by adding --ssl argument to the command line. This will turn on both client-server and server-server SSL support and disable non-SSL connections.

You might also want to take a look at zoocfg.tmpl template file before the Cheetah compile and make sure keystore/truststore location is correct and password is defined.

Generate self-signed certificate

```bash
keytool -genkeypair -alias $(hostname -f) -keyalg RSA -keysize 2048 -dname "cn=$(hostname -f)" -keypass password -keystore keystore.jks -storepass password
```

Export certificate from keystore

```bash
keytool -exportcert -alias $(hostname -f) -keystore keystore.jks -file $(hostname -f).cer -rfc
```

Import certiciate to truststore

```bash
keytool -importcert -file Andors-MacBook-Pro.local.cer -keystore truststore.jks
```

## Troubleshooting

It's possible to overload a machine when running lots of ZK ensemble members - if you run into an error such as "NoRouteToHostException: No valid address" you may need to update the ICMP rate limit which isset to 250 by default. You can turn this off using the following command:

```bash
sudo sysctl -wnet.inet.icmp.icmplim=0
```

(see also https://krypted.com/mac-os-x/disable-icmp-rate-limiting-os-x/)
