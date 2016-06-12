#!/usr/bin/python

import sys
import os

if __name__ == '__main__':
        data = {}
        print '<<<<<<<<<< start of configuration for all competition groups >>>>>>>>>>'
        print '\nPlease enter replication information:'

        sys.stdout.write( '\tVM template name: ')
        data['template_src'] = raw_input()

        sys.stdout.write( '\tVM template IP: ')
        data['template_ip'] = raw_input()

        sys.stdout.write( '\tVM template username (default: root): ')
        data['template_username'] = raw_input() or 'root'

        sys.stdout.write( '\tVM template password (default:op3nl@b): ')
        data['template_password'] = raw_input() or 'op3nl@b'

# Write config_vars

        f = open('./group_vars/all.yml', 'w')
        f.write('global:\n')
        for key, value in data.iteritems() :
            f.write('  ' + key + ': ' + value + '\n')
        f.close
        print '<<<<<<<<<< end of configuration for all competition groups >>>>>>>>>>'

        f = open('./inventory', 'w')
        entry = '{0} ansible_ssh_host={1} ansible_ssh_port=22 ansible_ssh_user={2} ansible_ssh_pass={3} ansible_sudo_pass={4}\n\n'. \
                 format(data['template_src'], data['template_ip'], data['template_username'], data['template_password'], data['template_password'])
        f.write(entry)
        f.close()
