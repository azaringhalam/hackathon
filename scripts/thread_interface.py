#!/usr/bin/python
'''
Created on Jan 18, 2016

@author: azaringh
'''
from jnpr.junos import Device
import json
import redis
import threading
import time
import datetime

window = 2999

# nap time is different for each router as they respond to poll with different latency.  The idea to poll each roughly every 30 seconds.
routers = [ 
           { 'name': 'chicago', 'ip': '10.10.11.27', 'router_id': '10.210.10.124', 'interfaces': [
                                                                                                  { 'name': 'ge-1/0/1', 'address': '10.210.16.2' }, 
                                                                                                  { 'name': 'ge-1/0/2', 'address': '10.210.13.2' },
                                                                                                  { 'name': 'ge-1/0/3', 'address': '10.210.14.2' }, 
                                                                                                  { 'name': 'ge-1/0/4', 'address': '10.210.17.2' }, 
                                                                                                  { 'name': 'ge-1/0/5', 'address': '' }, # attached to IXIA
                                                                                                  { 'name': 'ge-1/0/6', 'address': '' }, # attached to IXIA
                                                                                                  { 'name': 'ge-1/0/7', 'address': '' }  # attached to IXIA
                                                                                                  ], 
            'nap_time': 16 },
           { 'name': 'san francisco', 'ip': '10.10.10.52', 'router_id': '10.210.10.100', 'interfaces': [
                                                                                                        { 'name': 'ge-1/0/0', 'address': '10.210.18.1' },
                                                                                                        { 'name': 'ge-1/0/1', 'address': '10.210.15.1' },
                                                                                                        { 'name': 'ge-1/0/3', 'address': '10.210.16.1' },
                                                                                                        { 'name': 'xe-0/0/0', 'address': '' } # attached to Qfab
                                                                                                        ], 
            'nap_time': 21 },
           { 'name': 'dallas', 'ip': '10.10.10.53', 'router_id': '10.210.10.106', 'interfaces': [
                                                                                                 { 'name': 'ge-1/0/0', 'address': '10.210.15.2' }, 
                                                                                                 { 'name': 'ge-1/0/1', 'address': '10.210.19.1' }, 
                                                                                                 { 'name': 'ge-1/0/2', 'address': '10.210.21.1' }, 
                                                                                                 { 'name': 'ge-1/0/3', 'address': '10.210.11.1' }, 
                                                                                                 { 'name': 'ge-1/0/4', 'address': '10.210.13.1' }
                                                                                                 ], 
            'nap_time': 26 },
           { 'name': 'miami', 'ip': '10.10.10.55', 'router_id': '10.210.10.112', 'interfaces': [
                                                                                                { 'name': 'ge-1/0/0', 'address': '10.210.22.1' }, 
                                                                                                { 'name': 'ge-1/0/1', 'address': '10.210.24.1' }, 
                                                                                                { 'name': 'ge-1/0/2', 'address': '10.210.12.1' }, 
                                                                                                { 'name': 'ge-1/0/3', 'address': '10.210.11.2' }, 
                                                                                                { 'name': 'ge-1/0/4', 'address': '10.210.14.1' }
                                                                                                ], 
            'nap_time': 27 },
           { 'name': 'new york', 'ip': '10.10.11.25', 'router_id': '10.210.10.118', 'interfaces': [
                                                                                                   { 'name': 'ge-1/0/3', 'address': '10.210.12.2' }, 
                                                                                                   { 'name': 'ge-1/0/5', 'address': '10.210.17.1' }, 
                                                                                                   { 'name': 'ge-1/0/7', 'address': '10.210.26.1' }, 
                                                                                                   { 'name': 'xe-0/0/0', 'address': '' } # attached to Qfab
                                                                                                   ], 
            'nap_time': 22 },
           { 'name': 'los angeles', 'ip': '10.10.10.51', 'router_id': '10.210.10.113', 'interfaces': [
                                                                                                      { 'name': 'ge-1/0/0', 'address': '10.210.18.2' },
                                                                                                      { 'name': 'ge-1/0/1', 'address': '10.210.19.2' },
                                                                                                      { 'name': 'ge-1/0/2', 'address': '10.210.20.1' },
                                                                                                      { 'name': 'ge-1/0/3', 'address': '' } # attached to IXIA
                                                                                                      ], 
            'nap_time': 28 },
           { 'name': 'houston', 'ip': '10.10.10.54', 'router_id': '10.210.10.114', 'interfaces': [
                                                                                                  { 'name': 'ge-1/0/0', 'address': '10.210.20.2' },
                                                                                                  { 'name': 'ge-1/0/1', 'address': '10.210.21.2' },
                                                                                                  { 'name': 'ge-1/0/2', 'address': '10.210.22.2' },
                                                                                                  { 'name': 'ge-1/0/3', 'address': '10.210.25.1' },
                                                                                                  { 'name': 'ge-1/0/4', 'address': '' } # attached to IXIA
                                                                                                  ], 
            'nap_time': 27 },
           { 'name': 'tampa', 'ip': '10.10.10.56', 'router_id': '10.210.10.115', 'interfaces': [
                                                                                                { 'name': 'ge-1/0/0', 'address': '10.210.25.2' }, 
                                                                                                { 'name': 'ge-1/0/1', 'address': '10.210.24.2' }, 
                                                                                                { 'name': 'ge-1/0/2', 'address': '10.210.26.2' }, 
                                                                                                { 'name': 'ge-1/0/3', 'address': '' } # attached to IXIA
                                                                                                ], 
            'nap_time': 21 }
           ]

class interfaceThread(threading.Thread):
    def __init__(self, rtr, r):
        threading.Thread.__init__(self)
        self.rtr = rtr
        self.dev = ''
        self.redis = r
        
    def run(self):
        self.dev = Device(host=self.rtr['ip'], user='admin', password='op3nl@b')
        self.dev.open()
        while True:
            #t0 = time.clock()
            #t1 = time.time()
            for intf in self.rtr['interfaces']:
                intf_info = self.dev.rpc.get_interface_information({'format': 'json'},statistics=True, detail=True, interface_name=intf['name'])
                intf_counters_normal = { 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'), 
                                         'router_id': self.rtr['router_id'], 'interface_address': intf['address'],
                                         'stats':  intf_info['interface-information'][0]['physical-interface'][0]['traffic-statistics'] }
                jd = json.dumps(intf_counters_normal)
                dataset_normal = self.rtr['name'] + ':' + intf['name'] + ':traffic statistics'
                self.redis.lpush(dataset_normal,jd)
                self.redis.ltrim(dataset_normal, 0, window)
                
                intf_counters_input_errors = { 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'), 
                                               'router_id': self.rtr['router_id'], 'interface_address': intf['address'],
                                               'stats':  intf_info['interface-information'][0]['physical-interface'][0]['input-error-list'] }
                jd = json.dumps(intf_counters_input_errors)
                dataset_input_errors = self.rtr['name'] + ':' + intf['name'] + ':input-error-list'
                self.redis.lpush(dataset_input_errors,jd)
                self.redis.ltrim(dataset_input_errors, 0, window)
                
                intf_counters_output_errors = { 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'),
                                                'router_id': self.rtr['router_id'], 'interface_address': intf['address'], 
                                                'stats':  intf_info['interface-information'][0]['physical-interface'][0]['output-error-list'] }
                jd = json.dumps(intf_counters_output_errors)
                dataset_output_errors = self.rtr['name'] + ':' + intf['name'] + ':output-error-list'
                self.redis.lpush(dataset_output_errors,jd)
                self.redis.ltrim(dataset_output_errors, 0, window)
                
            time.sleep(self.rtr['nap_time'])   
            #print self.rtr['name'], len(self.rtr['interfaces']), ' cpu: ', (time.clock() - t0)
            #print self.rtr['name'], len(self.rtr['interfaces']), ' wall: ', (time.time() - t1) 
        print self.rtr['name'], ' interface polling thread exist'
        self.dev.close()

def main():
    all_threads = []
    r = redis.StrictRedis(host='10.10.4.252', port=6379, db=0)
    for rtr in routers:
        t = interfaceThread(rtr, r)
        t.start()
        all_threads.append(t)
        
    for t in all_threads:
        t.join()
            
if __name__ == '__main__':
    main()
