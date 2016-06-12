#!/usr/bin/python
'''
Created on May 13, 2016

@author: azaringh
'''
import sys
import os
import getopt
import json
import crypt
import struct, socket
from num2words import num2words

def main(argv):
    data = {}
    try:
        opts, args = getopt.getopt(argv, "hg:", ["help", "group_name="])
    except getopt.GetoptError:
        print 'group_config.py -g <group_name>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'group_config.py -g <group_name>'
            sys.exit()
        elif opt in ("-g", "--group_name"):
            group_name = arg
            
    print '<<<<<<<<<< start of group {0} configuration >>>>>>>>>>'.format(group_name)
    print 'Please enter vcenter information:'
    sys.stdout.write( '\tIP address: ')
    data['vcenter_hostname'] = raw_input()
    sys.stdout.write( '\tusername (default: root): ')
    data['vcenter_username'] = raw_input() or 'root'
    sys.stdout.write( '\tpassword (default: op3nl@b): ')
    data['vcenter_password'] = raw_input() or 'op3nl@b'

    print '\nPlease enter ESXi server information:'
    sys.stdout.write( '\tdatacenter name: ')
    data['esxi_datacenter'] = raw_input()
    sys.stdout.write( '\tserver IP: ')
    data['esxi_hostname'] = raw_input()
    sys.stdout.write( '\tusername (default: root): ')
    data['esxi_username'] = raw_input() or 'root'
    sys.stdout.write( '\tpassword (default: op3nl@b): ')
    data['esxi_password'] = raw_input() or 'op3nl@b'
    
    sys.stdout.write( '\tnumber of teams in the group: ')
    data['team_count'] = raw_input()
    
    sys.stdout.write( '\tbeginning team_number in group: ')
    data['first_team'] = raw_input()        

    sys.stdout.write( '\tbeginning team IP: ')
    data['first_ip'] = raw_input()

    sys.stdout.write( '\tVM root password: ')
    data['vm_root_password'] = raw_input()

    sys.stdout.write( '\tvswitch name East (default:vSwitch3): ')
    data['esxi_vswitch_east'] = raw_input() or 'vSwitch3'

    sys.stdout.write( '\tvswitch name West (default:vSwitch4): ')
    data['esxi_vswitch_west'] = raw_input() or 'vSwitch4'

    sys.stdout.write( '\tnic type (default: VMXNET3): ')
    data['nic_type'] = raw_input() or 'VMXNET3'

    sys.stdout.write( '\tnumber of vlans (other than management): ')
    data['num_vlan'] = raw_input()

    sys.stdout.write( '\tbase_vlan_id (default: 3000): ')
    data['base_vlan_id'] = raw_input() or '3000'

    ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
    int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
    team_ip_int = ip2int(data['first_ip'])

    f = open('./inventory', 'a')
    entry = '{0} ansible_ssh_host={1} ansible_ssh_port=22 ansible_ssh_user={2} ansible_ssh_pass={3} ansible_sudo_pass={4}\n'. \
             format('vcenter_host', data['vcenter_hostname'], data['vcenter_username'], data['vcenter_password'], data['vcenter_password'])
    f.write(entry)
    entry = '{0} ansible_ssh_host={1} ansible_ssh_port=22 ansible_ssh_user={2} ansible_ssh_pass={3} ansible_sudo_pass={4}\n'. \
             format('esxi_host', data['esxi_hostname'], data['esxi_username'], data['esxi_password'], data['esxi_password'])
    f.write(entry + '\n')

    f.write('[' + group_name + ']\n')

    num_to_name = []
    for i in range(0, int(data['team_count'])):
      num_to_name.append(num2words(i+1))
    ip_list_east = []
    ip_list_west = []
    for team_num in range(int(data['first_team']), int(data['first_team']) + int(data['team_count'])):
        team_ip_east = int2ip(team_ip_int)
        team_ip_west = int2ip(team_ip_int + 20) # offset east and west management IPs by 20
        ip_list_east.append(team_ip_east)
        ip_list_west.append(team_ip_west)
        team_ip_int = team_ip_int + 1
        team_name_east = 'group' + num2words(team_num) + '-east'
        team_name_west = 'group' + num2words(team_num) + '-west'
        entry = '{0} ansible_ssh_host={1} ansible_ssh_port=22 ansible_ssh_user={2} ansible_ssh_pass={3} ansible_sudo_pass={4}\n'. \
                 format(team_name_east, team_ip_east, 'root', data['vm_root_password'], data['vm_root_password'])
        f.write(entry)
        entry = '{0} ansible_ssh_host={1} ansible_ssh_port=22 ansible_ssh_user={2} ansible_ssh_pass={3} ansible_sudo_pass={4}\n'. \
                 format(team_name_west, team_ip_west, 'root', data['vm_root_password'], data['vm_root_password'])
        f.write(entry)
 
    f.close()

    f = open('./group_vars/' + group_name + '.yml', 'w')
    f.write(group_name + ':\n')
    hosts = []
    coast_name = [ 'east', 'west']
    ip_list = [ ip_list_east, ip_list_west ]
    vswitch_list = [ data['esxi_vswitch_east'], data['esxi_vswitch_west'] ]
    for coast in range(2):
      for i in range(0, int(data['team_count'])):
        first_vlan = int(data['base_vlan_id']) + 10 * (i + 1) +  4 * coast + 1
        vlist = [ { 'vlan_id' : (j + first_vlan), 'vlan_name': 'group-' + num2words(i+1) + '-' + coast_name[coast] + '-' + str(j + first_vlan), \
	            'ip_address': '192.168.' + str(j + 1) + '.' + str(coast + 1) }  for j in range(int(data['num_vlan'])) ]
        nic_list = {}
        for h in range(int(data['num_vlan'])):
          nic = { 'network': vlist[h]['vlan_name'],  'type': 'VMXNET3', 'network_type': 'standard' }
	  nic_list['nic'+ str(h +2)] = nic
  
        #encrypted_password = crypt.crypt('Group' + '-' + num2words(i+1).title(), '$1$HackaThon$')
        dict_item = { 'hostname': 'group' + num2words(i+1)  + '-' + coast_name[coast], 'ip_address': ip_list[coast][i],  \
                      'username': 'group' + '-' + num2words(i+1), 'password': 'Group-' + num2words(i+1).title(), \
                      'vlan_list': vlist, 'nic_list': nic_list, 'vswitch':  vswitch_list[coast] }
        hosts.append(dict_item)
    
    f.write('  host_list: ' + json.dumps(hosts) + '\n')
    for key, value in data.iteritems() :
        f.write('  ' + key + ': ' + value + '\n')
    f.close
        
if __name__ == '__main__':
    main(sys.argv[1:])
