#!/usr/bin/python
'''
Created on Mar 21, 2016

@author: azaringh
'''
import atexit
import sys
import getopt

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect

def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def main(argv):
    inputs = {}
    try:
        opts, args = getopt.getopt(argv, "hi:u:p:e:s:v:n:", \
               ["help", "vcenter_ip=", "username=", "password=", "esxi_host=", "vlan_name="])
    except getopt.GetoptError:
        print 'remove_vlan.py -i <vcenter_ip> -u <username> -p <password> -e <esxi_host> -n <vlan_name>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'remove_vlan.py -i <vcenter_ip> -u <username> -p <password> -e <esxi_host> -n <vlan_name>'
            sys.exit()
        elif opt in ("-i", "--vcenter_ip"):
            inputs['vcenter_ip'] = arg
        elif opt in ("-u", "--username"):
            inputs['vcenter_user'] = arg
        elif opt in ("-p", "--password"):
            inputs['vcenter_password'] = arg
        elif opt in ("-e", "--esxi_host"):
            inputs['host_name'] = arg
        elif opt in ("-n", "--vlan_name"):
            inputs['port_group_name'] = arg
    try:
        si = None
        try:
            print "Trying to connect to VCENTER SERVER . . ."
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'], version="vim.version.version8")
        except IOError, e:
            pass
            atexit.register(Disconnect, si)
        print "Connected to VCENTER SERVER !"
        content = si.RetrieveContent()
        host = get_obj(content, [vim.HostSystem], inputs['host_name'])
        host_network_system = host.configManager.networkSystem
        host_network_system.RemovePortGroup(pgName=inputs['port_group_name'])
        print "Successfully removed PortGroup ",  inputs['port_group_name']

    except vmodl.MethodFault, e:
	if e.msg == 'The object or item referred to could not be found.':
	  print "VLAN does not exist"
	  return 0
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1

if __name__ == "__main__":
    main(sys.argv[1:])
