#!/usr/bin/python
'''
Created on Feb 19, 2016

@author: azaringh
'''
'''
Created on Feb 19, 2016

@author: azaringh
'''
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
import threading
import random
import time
import datetime
import os
import json
import redis

routers = [
           { 'name': 'chicago', 'ip': '10.10.11.27', 'router_id': '10.210.10.124', 'interfaces': [
                                                                                                  { 'name': 'ge-1/0/1', 'address': '10.210.16.2' },
                                                                                                  { 'name': 'ge-1/0/2', 'address': '10.210.13.2' },
                                                                                                  { 'name': 'ge-1/0/3', 'address': '10.210.14.2' },
                                                                                                  { 'name': 'ge-1/0/4', 'address': '10.210.17.2' }
                                                                                                  ]
            },
           { 'name': 'san francisco', 'ip': '10.10.10.52', 'router_id': '10.210.10.100', 'interfaces': [
                                                                                                        { 'name': 'ge-1/0/0', 'address': '10.210.18.1' },
                                                                                                        { 'name': 'ge-1/0/1', 'address': '10.210.15.1' },
                                                                                                        { 'name': 'ge-1/0/3', 'address': '10.210.16.1' }
                                                                                                        ]
            },
           { 'name': 'dallas', 'ip': '10.10.10.53', 'router_id': '10.210.10.106', 'interfaces': [
                                                                                                 { 'name': 'ge-1/0/0', 'address': '10.210.15.2' },
                                                                                                 { 'name': 'ge-1/0/1', 'address': '10.210.19.1' },
                                                                                                 { 'name': 'ge-1/0/2', 'address': '10.210.21.1' },
                                                                                                 { 'name': 'ge-1/0/3', 'address': '10.210.11.1' },
                                                                                                 { 'name': 'ge-1/0/4', 'address': '10.210.13.1' }
                                                                                                 ]
            },
           { 'name': 'miami', 'ip': '10.10.10.55', 'router_id': '10.210.10.112', 'interfaces': [
                                                                                                { 'name': 'ge-1/0/0', 'address': '10.210.22.1' },
                                                                                                { 'name': 'ge-1/0/1', 'address': '10.210.24.1' },
                                                                                                { 'name': 'ge-1/0/2', 'address': '10.210.12.1' },
                                                                                                { 'name': 'ge-1/0/3', 'address': '10.210.11.2' },
                                                                                                { 'name': 'ge-1/0/4', 'address': '10.210.14.1' }
                                                                                                ]
            },
           { 'name': 'new york', 'ip': '10.10.11.25', 'router_id': '10.210.10.118', 'interfaces': [
                                                                                                   { 'name': 'ge-1/0/3', 'address': '10.210.12.2' },
                                                                                                   { 'name': 'ge-1/0/5', 'address': '10.210.17.1' },
                                                                                                   { 'name': 'ge-1/0/7', 'address': '10.210.26.1' }
                                                                                                   ]
            },
           { 'name': 'los angeles', 'ip': '10.10.10.51', 'router_id': '10.210.10.113', 'interfaces': [
                                                                                                      { 'name': 'ge-1/0/0', 'address': '10.210.18.2' },
                                                                                                      { 'name': 'ge-1/0/1', 'address': '10.210.19.2' },
                                                                                                      { 'name': 'ge-1/0/2', 'address': '10.210.20.1' }
                                                                                                      ]
            },
           { 'name': 'houston', 'ip': '10.10.10.54', 'router_id': '10.210.10.114', 'interfaces': [
                                                                                                  { 'name': 'ge-1/0/0', 'address': '10.210.20.2' },
                                                                                                  { 'name': 'ge-1/0/1', 'address': '10.210.21.2' },
                                                                                                  { 'name': 'ge-1/0/2', 'address': '10.210.22.2' },
                                                                                                  { 'name': 'ge-1/0/3', 'address': '10.210.25.1' }
                                                                                                  ]
            },
           { 'name': 'tampa', 'ip': '10.10.10.56', 'router_id': '10.210.10.115', 'interfaces': [
                                                                                                { 'name': 'ge-1/0/0', 'address': '10.210.25.2' },
                                                                                                { 'name': 'ge-1/0/1', 'address': '10.210.24.2' },
                                                                                                { 'name': 'ge-1/0/2', 'address': '10.210.206.2' }
                                                                                                ]
            }
           ]

class LinkFailureModel(threading.Thread):
    def __init__(self, rtr, MTTF, MTTR):
        threading.Thread.__init__(self)
        self.rtr = rtr
        self.MTTF = MTTF
        self.MTTR = MTTR
        self.logfile = ''
        self.redis = redis.StrictRedis(host='10.10.4.252', port=6379, db=0)

    def failed(self):
        return random.random() <= 1.0/self.MTTF

    def repaired(self):
        return random.random() <= 1.0/self.MTTR

    def run(self):
        self.logfile = open(os.getcwd() + '/' + 'linkfailure_log', 'a')
        while True:
            while self.failed() == False:
                time.sleep(1)
            # select a router
            r_number = random.randint(1,len(self.rtr)) - 1
            # select a random interface 
            i_number = random.randint(1, len(self.rtr[r_number]['interfaces'])) - 1

            #set interfaces ge-1/0/3 disable 

            cmd = 'set interfaces ' + self.rtr[r_number]['interfaces'][i_number]['name'] + ' disable'

            dev = Device(host=self.rtr[r_number]['ip'], user='root', password='juniper123')
            dev.open()
            dev.timeout = 60
            cu = Config(dev)
            cu.lock()
            cu.load(cmd, format='set', merge=True)
            cu.commit()
            cu.unlock()
            dev.close()
            link__data = { 'status': 'failed', 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'), 
                                'router_id': self.rtr[r_number]['router_id'], 'router_name': self.rtr[r_number]['name'],
                                'interface_address': self.rtr[r_number]['interfaces'][i_number]['address'],
                                'interface_name': self.rtr[r_number]['interfaces'][i_number]['name']
                         }
            jd = json.dumps(link__data)
            self.redis.publish('link_event', jd)
            self.logfile.write("Link failed: " + datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S') + " " +
                               self.rtr[r_number]['name'] + " " +  self.rtr[r_number]['ip'] + " " + self.rtr[r_number]['interfaces'][i_number]['name'] + "\n")
            self.logfile.flush()
            # now repair the link
            while self.repaired() == False:
                time.sleep(1)

            cmd = 'delete interfaces ' + self.rtr[r_number]['interfaces'][i_number]['name'] + ' disable'
            dev = Device(host=self.rtr[r_number]['ip'], user='root', password='juniper123')
            dev.open()
            dev.timeout = 60
            cu = Config(dev)
            cu.lock()
            cu.load(cmd, format='set', merge=True)
            cu.commit()
            cu.unlock()
            dev.close()
            link__data = { 'status': 'healed', 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'), 
                                'router_id': self.rtr[r_number]['router_id'], 'router_name': self.rtr[r_number]['name'],
                                'interface_address': self.rtr[r_number]['interfaces'][i_number]['address'],
                                'interface_name': self.rtr[r_number]['interfaces'][i_number]['name']
                         }
            jd = json.dumps(link__data)
            self.redis.publish('link_event', jd)
            self.logfile.write("Link healed: " + datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S') + " " +
                               self.rtr[r_number]['name'] + " " +  self.rtr[r_number]['ip'] + " " + self.rtr[r_number]['interfaces'][i_number]['name'] + "\n")
            self.logfile.flush()


MTTF = 7200.0 # on average one failure every two hours
MTTR = 300.0  # on average 5 minutes to repair

def main():
    t = LinkFailureModel(routers, MTTF, MTTR)
    t.start()
    t.join()


if __name__ == '__main__':
    main()
                                     
