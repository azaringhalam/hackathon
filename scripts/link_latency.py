#!/usr/bin/python
'''
Created on Feb 27, 2016

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
                                                                                                  { 'name': 'ge-1/0/1', 'address': '10.210.16.2', 'to': 'san francisco' }, 
                                                                                                  { 'name': 'ge-1/0/2', 'address': '10.210.13.2', 'to': 'dallas' },
                                                                                                  { 'name': 'ge-1/0/3', 'address': '10.210.14.2', 'to': 'miami' }, 
                                                                                                  { 'name': 'ge-1/0/4', 'address': '10.210.17.2', 'to':  'new york'}
                                                                                                  ], 
            'nap_time': 16 },
           { 'name': 'san francisco', 'ip': '10.10.10.52', 'router_id': '10.210.10.100', 'interfaces': [
                                                                                                        { 'name': 'ge-1/0/0', 'address': '10.210.18.1', 'to': 'los angeles' },
                                                                                                        { 'name': 'ge-1/0/1', 'address': '10.210.15.1', 'to': 'dallas' },
                                                                                                        { 'name': 'ge-1/0/3', 'address': '10.210.16.1', 'to': 'chicago' }
                                                                                                        ], 
            'nap_time': 21 },
           { 'name': 'dallas', 'ip': '10.10.10.53', 'router_id': '10.210.10.106', 'interfaces': [
                                                                                                 { 'name': 'ge-1/0/0', 'address': '10.210.15.2', 'to': 'san francisco' }, 
                                                                                                 { 'name': 'ge-1/0/1', 'address': '10.210.19.1', 'to': 'los angeles' }, 
                                                                                                 { 'name': 'ge-1/0/2', 'address': '10.210.21.1', 'to': 'houston' }, 
                                                                                                 { 'name': 'ge-1/0/3', 'address': '10.210.11.1', 'to': 'miami' }, 
                                                                                                 { 'name': 'ge-1/0/4', 'address': '10.210.13.1', 'to': 'chicago' }
                                                                                                 ], 
            'nap_time': 26 },
           { 'name': 'miami', 'ip': '10.10.10.55', 'router_id': '10.210.10.112', 'interfaces': [
                                                                                                { 'name': 'ge-0/1/0', 'address': '10.210.22.1', 'to': 'houston' }, 
                                                                                                { 'name': 'ge-0/1/1', 'address': '10.210.24.1', 'to': 'tampa' }, 
                                                                                                { 'name': 'ge-0/1/2', 'address': '10.210.12.1', 'to': 'new york' }, 
                                                                                                { 'name': 'ge-0/1/3', 'address': '10.210.11.2', 'to': 'dallas' }, 
                                                                                                { 'name': 'ge-1/3/0', 'address': '10.210.14.1', 'to': 'chicago' }
                                                                                                ], 
            'nap_time': 27 },
           { 'name': 'new york', 'ip': '10.10.11.25', 'router_id': '10.210.10.118', 'interfaces': [
                                                                                                   { 'name': 'ge-1/0/3', 'address': '10.210.12.2', 'to': 'miami' }, 
                                                                                                   { 'name': 'ge-1/0/5', 'address': '10.210.17.1', 'to': 'chicago' }, 
                                                                                                   { 'name': 'ge-1/0/7', 'address': '10.210.26.1', 'to': 'tampa' } 
                                                                                                   ], 
            'nap_time': 22 },
           { 'name': 'los angeles', 'ip': '10.10.10.51', 'router_id': '10.210.10.113', 'interfaces': [
                                                                                                      { 'name': 'ge-0/1/0', 'address': '10.210.18.2', 'to': 'san francisco' },
                                                                                                      { 'name': 'ge-0/1/1', 'address': '10.210.19.2', 'to': 'dallas' },
                                                                                                      { 'name': 'ge-0/1/2', 'address': '10.210.20.1', 'to': 'houston' }
                                                                                                      ], 
            'nap_time': 28 },

#           { 'name': 'houston', 'ip': '10.10.10.54', 'router_id': '10.210.10.114', 'interfaces': [
#                                                                                                 { 'name': 'ge-0/1/0', 'address': '10.210.20.2', 'to': 'los angeles' },
#                                                                                                 { 'name': 'ge-0/1/1', 'address': '10.210.21.2', 'to': 'dallas' },
#                                                                                                  { 'name': 'ge-0/1/2', 'address': '10.210.22.2', 'to': 'miami' },
#                                                                                                 { 'name': 'ge-0/1/3', 'address': '10.210.25.1', 'to': 'tampa' }
#                                                                                                ], 
#          'nap_time': 27 },
           { 'name': 'tampa', 'ip': '10.10.10.56', 'router_id': '10.210.10.115', 'interfaces': [
                                                                                                { 'name': 'ge-1/0/0', 'address': '10.210.25.2', 'to': 'houston' }, 
                                                                                                { 'name': 'ge-1/0/1', 'address': '10.210.24.2', 'to': 'miami' }, 
                                                                                                { 'name': 'ge-1/0/2', 'address': '10.210.26.2', 'to': 'new york'} 
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
            if self.rtr['name'] == 'houston':
                continue
            for intf in self.rtr['interfaces']:
                try:
                    result = self.dev.rpc.ping({'format': 'json'},host=intf['address'], count='1')
                    latency = { 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%a:%H:%M:%S'), 
                                             'from-router': self.rtr['name'], 'to-router': intf['to'],
                                             'rtt-average(ms)':  float(result['ping-results'][0]['probe-results-summary'][0]['rtt-average'][0]['data'])/1000.0 }
                    jd = json.dumps(latency)
                    dataset = self.rtr['name'] + ':' + intf['to'] + ':latency'
                    self.redis.lpush(dataset,jd)
                    self.redis.ltrim(dataset, 0, window)
                except:
                    print self.rtr['name'], intf['address'], ' latency polling failed'
                    continue
                
            print self.rtr['name'], ' latency thread exist'
            time.sleep(self.rtr['nap_time'])   
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
