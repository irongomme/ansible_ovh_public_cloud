#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

import ConfigParser
import json
import ovh
import os


class OvhPublicCloudInventory:

    # Inventory
    inventory = {'_meta': {'hostvars': {}}}

    def __init__(self):
        ''' Construct inventory '''

        # Configuration file
        config_file = 'ovh_public_cloud.conf'
        current_path = os.path.dirname(os.path.abspath(__file__))

        # Configuration reading
        self.config = ConfigParser.RawConfigParser()
        self.config.read('%s/%s' % (current_path, config_file))

        # OVH API client
        self.api = ovh.Client(config_file='%s/%s' % (current_path, config_file))

        # Generate inventory
        self.generate()


    def __str__(self):
        ''' Inventory JSON output '''

        return json.dumps(self.inventory, sort_keys=True, indent=4)


    def generate(self):
        ''' Generation for cloud instances inventory '''

        # For each public cloud project
        for project_id in self.api.get('/cloud/project'):

            # For each instance group
            for group in self.api.get('/cloud/project/%s/instance/group' % (project_id)):
                self.add_group(project_id, group)

            # For each instance
            for instance in self.api.get('/cloud/project/%s/instance' % (project_id)):
                self.add_instance(project_id, instance)


    def add_group(self, project_id, group):
        ''' Add instances into groups '''

        # Groups names from current group
        instance_groups = (group['id'], group['name'], '%s_%s' % (group['name'], group['region']))

        # For every intance id of current group
        for instance_id in group['instance_ids']:

            # Allocate instances into those groups
            for instance_group in instance_groups:
                self.inventory.setdefault(instance_group, []).append(instance_id)


    def add_instance(self, project_id, instance):
        ''' Add instance details for use with ansible '''

        # Instance flavor
        flavor = self.api.get('/cloud/project/%s/flavor/%s' %
                            (project_id, instance['flavorId']))

        # Instance os image
        image = self.api.get('/cloud/project/%s/image/%s' %
                           (project_id, instance['imageId']))

        # Allocate instance into new groups
        for instance_group in (project_id, instance['region'], image['type'], flavor['name'],
                               image['name'].replace(' ', '').lower(), 'ovh_public_cloud', ):
            self.inventory.setdefault(instance_group, []).append(instance['id'])

        # Instance details for inventory
        self.inventory['_meta']['hostvars'][instance['id']] = {
            'ansible_ssh_user': image['user'],
            'ansible_ssh_host': self.get_address(instance['ipAddresses']),
            'hostname': instance['name'],
            'openstack': instance
        }


    def get_address(self, interfaces):
        ''' Get instance ip address '''
        address = None

        # Kind of default network, or public if unspecified
        network_type = self.config.get('openstack', 'openstack_network_default') or 'public'

        # Use of IPV6 or not
        use_ipv6 = self.config.getboolean('openstack', 'openstack_network_ipv6') or False

        # Browse network interfaces
        for interface in interfaces:

            # Does interface match configuration
            is_address_version = interface['version'] == 6 if use_ipv6 else 4
            is_interface_type = interface['type'] == network_type

            # If interface doesn't match, we keep the first found
            # with a preference for the one matching the ipv6 choice
            if (is_address_version and is_interface_type) \
               or (is_address_version and address == None) or address == None:
                address = interface['ip']

        return address


# Launch generation
if __name__ == '__main__':
    print OvhPublicCloudInventory()
