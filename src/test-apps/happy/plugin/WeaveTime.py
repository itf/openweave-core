#!/usr/bin/env python


#
#    Copyright (c) 2016-2017 Nest Labs, Inc.
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

#
#    @file
#       Implements WeaveTime class that tests Weave Time sync among Weave Nodes.
#

import os
import sys
import time

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
from happy.HappyNetwork import HappyNetwork
from plugin.WeaveTest import WeaveTest


options = {
    "client": None,
    "coordinator": None,
    "server": None,
    "mode": "auto",
    "quiet": False,
    "tap": None,
    "skip_service_end": False,
    "skip_coordinator_end": False,
    "client_faults": False,
    "server_faults": False,
    "coordinator_faults": False,
    "iterations": None,
    "test_tag": ""
}


def option():
    return options.copy()


class WeaveTime(HappyNode, HappyNetwork, WeaveTest):
    """
    weave-time [-h --help] [-q --quiet] [-c --client <NAME>] [-o --coordinator <NAME>]
               [-s --server <NAME>] [-m --mode <MODE>] [-p --tap <TAP_INTERFACE>]
               [--client_faults <fault-injection configuration>]
               [--server_faults <fault-injection configuration>]
               [--coordinator_faults <fault-injection configuration>]

    commands to test Time profile:
        $ weave-time -c node01 -o node02 -s node03 -m auto
            Time sync test among client(node01), coordinator(node02) and server(node03) with Auto mode (multicast)

        $ weave-time -c node01 -o node02 -s node03 -m local
            Time sync test among client(node01), coordinator(node02) and server(node03) with Local mode (udp)

        $ weave-time -c node01 -o node02 -s node03 -m service
            Time sync test among client(node01), coordinator(node02) and server(node03) with Service mode (tcp)

    Note:
        There are four time sync modes:
         - auto: time sync via Multicast (default)
         - local: time sync with local nodes via UDP
         - service: time sync with Service via TCP
         - service-over-tunnel: time sync with service via WRM over a weave tunnel

    return:
        0   success
        1   failure

    """
    def __init__(self, opts = options):
        HappyNode.__init__(self)
        HappyNetwork.__init__(self)
        WeaveTest.__init__(self)

        self.__dict__.update(options)
        self.__dict__.update(opts)

        self.client_process_tag = "WEAVE-TIME-CLIENT" + opts.get("test_tag")
        self.coordinator_process_tag = "WEAVE-TIME-COORDINATOR" + opts.get("test_tag")
        self.server_process_tag = "WEAVE-TIME-SERVER" + opts.get("test_tag")

        self.client_node_id = None
        self.coordinator_node_id = None
        self.server_node_id = None


    def __pre_check(self):
        # Check if Weave Time client node is given.
        if self.client == None:
            emsg = "Missing name or address of the Weave Time client node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        # Check if Weave Time coordinator node is given.
        if not self.skip_coordinator_end and self.coordinator == None:
            emsg = "Missing name or address of the Weave Time coordinator node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        # Check if Weave Time server node is given.
        if self.server == None:
            emsg = "Missing name or address of the Weave Time server node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)


        # Make sure that fabric was created
        if self.getFabricId() == None:
            emsg = "Weave Fabric has not been created yet."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        # Check if Weave Time client node exists.
        if self._nodeExists(self.client):
            self.client_node_id = self.client

        # Check if Weave Time coordinator node exists.
        if self._nodeExists(self.coordinator):
            self.coordinator_node_id = self.coordinator

        # Check if Weave Time server node exists.
        if self._nodeExists(self.server):
            self.server_node_id = self.server

        if self.client_node_id == None:
            emsg = "Unknown identity of the client node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if not self.skip_coordinator_end and self.coordinator_node_id == None:
            emsg = "Unknown identity of the coordinator node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if self.server_node_id == None and self.server != "service":
            emsg = "Unknown identity of the server node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        self.client_ip = self.getNodeWeaveIPAddress(self.client_node_id)
        self.client_weave_id = self.getWeaveNodeID(self.client_node_id)

        if not self.skip_coordinator_end:
            self.coordinator_ip = self.getNodeWeaveIPAddress(self.coordinator_node_id)
            self.coordinator_weave_id = self.getWeaveNodeID(self.coordinator_node_id)

        if self.server == "service":
            self.skip_service_end = True
            self.server_weave_id = self.getServiceWeaveID("Time")
            self.server_ip = self.getServiceWeaveIPAddress("Time")
        else:
            self.server_ip = self.getNodeWeaveIPAddress(self.server_node_id)
            self.server_weave_id = self.getWeaveNodeID(self.server_node_id)

        # Check if all unknowns were found

        if self.client_ip == None:
            emsg = "Could not find IP address of the client node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if not self.skip_coordinator_end and self.coordinator_ip == None:
            emsg = "Could not find IP address of the coordinator node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if self.server_ip == None:
            emsg = "Could not find IP address of the server node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if self.client_weave_id == None:
            emsg = "Could not find Weave node ID of the client node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if not self.skip_coordinator_end and self.coordinator_weave_id == None:
            emsg = "Could not find Weave node ID of the coordinator node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)

        if self.server_weave_id == None:
            emsg = "Could not find Weave node ID of the server node."
            self.logger.error("[localhost] WeaveTime: %s" % (emsg))
            sys.exit(1)


    def __process_results(self, output):
        pass_test = False

        for line in output.split("\n"):
            if "Sync Succeeded" in line:
                pass_test = True
                break

        if not self.skip_coordinator_end:
            print "weave-time test among server %s (%s), client %s (%s), coordinator %s (%s) with %s mode: " % \
                        (self.server_node_id, self.server_ip,
                         self.client_node_id, self.client_ip,
                         self.coordinator_node_id, self.coordinator_ip, self.mode)
        else:
            print "weave-time test among server %s (%s), client %s (%s) with %s mode: " % \
                        (self.server_node_id, self.server_ip,
                         self.client_node_id, self.client_ip, self.mode)

        if self.quiet == False:
            if pass_test:
                print hgreen("Time sync succeeded")
            else:
                print hred("Time sync failed")

        return (pass_test, output)


    def __start_client_side(self):
        cmd = self.getWeaveMockDevicePath()
        if not cmd:
            return

        cmd += " --debug-resource-usage --print-fault-counters"
        cmd += " --node-addr " + self.client_ip
        cmd += " --time-sync-client"

        if self.mode == "local":
            cmd += " --time-sync-mode-local" 
        elif self.mode == "service":                 ## TCP
            cmd += " --time-sync-mode-service"
        elif self.mode == "service-over-tunnel":     ## WRM over tunnel
            cmd += " --time-sync-mode-service-over-tunnel"
            cmd += " --ts-server-node-id " + self.server_weave_id
            cmd += " --ts-server-node-addr " + self.server_ip
        else: 
            cmd += " --time-sync-mode-auto" 

        if self.tap:
            cmd += " --interface " + self.tap

        if self.client_faults:
            cmd += " --faults " + self.client_faults

        if self.iterations:
            cmd += " --iterations " + str(self.iterations)

        #self.start_weave_process(self.client_node_id, cmd, self.client_process_tag, sync_on_output=self.ready_to_service_events_str)
        self.start_weave_process(self.client_node_id, cmd, self.client_process_tag, sync_on_output="Sync Succeeded")


    def __stop_client_side(self):
        self.stop_weave_process(self.client_node_id, self.client_process_tag)

  
    def __start_coordinator_side(self):
        cmd = self.getWeaveMockDevicePath()
        if not cmd:
            return

        cmd += " --debug-resource-usage --print-fault-counters"
        cmd += " --node-addr " + self.coordinator_ip
        cmd += " --time-sync-coordinator"

        if self.tap:
            cmd += " --interface " + self.tap

        if self.coordinator_faults:
            cmd += " --faults " + self.coordinator_faults

        self.start_weave_process(self.coordinator_node_id, cmd, self.coordinator_process_tag, sync_on_output=self.ready_to_service_events_str)

    def __stop_coordinator_side(self):
        self.stop_weave_process(self.coordinator_node_id, self.coordinator_process_tag)


    def __start_server_side(self):
        cmd = self.getWeaveMockDevicePath()
        if not cmd:
            return

        cmd += " --debug-resource-usage --print-fault-counters"
        cmd += " --node-addr " + self.server_ip
        cmd += " --time-sync-server"

        if self.tap:
            cmd += " --interface " + self.tap

        if self.server_faults:
            cmd += " --faults " + self.server_faults

        self.start_weave_process(self.server_node_id, cmd, self.server_process_tag, sync_on_output=self.ready_to_service_events_str)

    def __stop_server_side(self):
        self.stop_weave_process(self.server_node_id, self.server_process_tag)


    def run(self):
        self.logger.debug("[localhost] WeaveTime: Run.")

        self.__pre_check()

        if self.mode == "auto":
            # run a normal case (multicast)
            self.__start_server_side()
            self.__start_coordinator_side()
            self.__start_client_side()

            # reserve enough time for the whole time sync procedure
            # There is a 30 seconds timer to trigger HandleUnreliableAfterBootTimer (WEAVE_CONFIG_TIME_SERVER_TIMER_UNRELIABLE_AFTER_BOOT_MSEC)
            # time.sleep(40)

            # run a TimeChangeNotification case
            self.__stop_server_side()
            self.__start_server_side()
            time.sleep(3)

        elif self.mode == "service-over-tunnel":
            self.__start_client_side()
            time.sleep(40)

        else:
            self.__start_server_side()
            self.__start_coordinator_side()
            self.__start_client_side()

        self.__stop_client_side()

        if not self.skip_coordinator_end:
            self.__stop_coordinator_side()

        if not self.skip_service_end:
            self.__stop_server_side()

        client_output_value, client_output_data = \
            self.get_test_output(self.client_node_id, self.client_process_tag, True)
        client_strace_value, client_strace_data = \
            self.get_test_strace(self.client_node_id, self.client_process_tag, True)

        if self.skip_coordinator_end:
            coordinator_output_data = ""
            coordinator_output_value = 0
            coordinator_strace_data = ""
            coordinator_strace_value = 0
        else:
            coordinator_output_value, coordinator_output_data = \
                self.get_test_output(self.coordinator_node_id, self.coordinator_process_tag, True)
            coordinator_strace_value, coordinator_strace_data = \
                self.get_test_strace(self.coordinator_node_id, self.coordinator_process_tag, True)

        if self.skip_service_end:
            server_output_data = ""
            server_output_value = 0
            server_strace_data = ""
            server_strace_value = 0
        else:
            server_output_value, server_output_data = \
                    self.get_test_output(self.server_node_id, self.server_process_tag, True)
            server_strace_value, server_strace_data = \
                    self.get_test_strace(self.server_node_id, self.server_process_tag, True)

        avg, results = self.__process_results(client_output_data)

        data = {}
        data["client_output"] = client_output_data
        data["client_strace"] = client_strace_data
        data["coordinator_output"] = coordinator_output_data
        data["coordinator_strace"] = coordinator_strace_data
        data["server_output"] = server_output_data
        data["server_strace"] = server_strace_data

        self.logger.debug("[localhost] WeaveTime: Done.")

        return ReturnMsg(avg, data)
