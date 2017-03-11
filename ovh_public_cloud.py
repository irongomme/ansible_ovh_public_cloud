#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

import ConfigParser
import json
import ovh
import os


class OvhPublicCloudInventory:

    # Inventaire
    inventory = {'_meta': {'hostvars': {}}}

    def __init__(self):
        ''' Construction de l'inventaire '''

        # Variable pour le fichier de configuration
        config_file = 'ovh_public_cloud.conf'
        current_path = os.path.dirname(os.path.abspath(__file__))

        # Lecture de la configuration
        self.config = ConfigParser.RawConfigParser()
        self.config.read('%s/%s' % (current_path, config_file))

        # Instanciation du client OVH
        self.api = ovh.Client(config_file='%s/%s' % (current_path, config_file))

        # Génération de l'inventaire
        self.generate()


    def __str__(self):
        ''' Sortie json de l'inventaire '''

        return json.dumps(self.inventory, sort_keys=True, indent=4)


    def generate(self):
        ''' Construction de l'inventaire des instances '''

        # Pour chaque projet cloud
        for project_id in self.api.get('/cloud/project'):

            # Pour chaque groupe du projet cloud
            for group in self.api.get('/cloud/project/%s/instance/group' % (project_id)):
                self.add_group(project_id, group)

            # Pour chaque instance du projet cloud
            for instance in self.api.get('/cloud/project/%s/instance' % (project_id)):
                self.add_instance(project_id, instance)


    def add_group(self, project_id, group):
        ''' Ajout des groupes d'instances et de la répartition des instances à l'intérieur '''

        # Les différents groupes découlant de celui envoyé
        instance_groups = (group['id'], group['name'], '%s_%s' % (group['name'], group['region']))

        # Toutes les instances du projet
        for instance_id in group['instance_ids']:

            # Association des instances par groupe
            for instance_group in instance_groups:
                self.inventory.setdefault(instance_group, []).append(instance_id)


    def add_instance(self, project_id, instance):
        ''' Ajout des infos de l'instance pour l'utilisation avec ansible '''

        # Modèle d'instance
        flavor = self.api.get('/cloud/project/%s/flavor/%s' %
                            (project_id, instance['flavorId']))

        # Image du système
        image = self.api.get('/cloud/project/%s/image/%s' %
                           (project_id, instance['imageId']))

        # Affectation des id d'instances dans chacun des nouveaux groupes
        for instance_group in (project_id, instance['region'], image['type'], flavor['name'],
                               image['name'].replace(' ', '').lower(), 'ovh_public_cloud', ):
            self.inventory.setdefault(instance_group, []).append(instance['id'])

        # Détail des instances dans l'inventaire
        self.inventory['_meta']['hostvars'][instance['id']] = {
            'ansible_ssh_user': image['user'],
            'ansible_ssh_host': self.get_address(instance['ipAddresses']),
            'hostname': instance['name'],
            'openstack': instance
        }


    def get_address(self, interfaces):
        ''' Obention de l'adresse ip de l'instance '''
        address = None

        # Type d'interface réseau par défaut ou public si non spécifié
        network_type = self.config.get('openstack', 'openstack_network_default') or 'public'

        # Utilisation d'IPV6 ou pas
        use_ipv6 = self.config.getboolean('openstack', 'openstack_network_ipv6') or False

        # Parcours des interfaces
        for interface in interfaces:

            # Est-ce que l'interface correspond à la configuration
            is_address_version = interface['version'] == 6 if use_ipv6 else 4
            is_interface_type = interface['type'] == network_type

            # Si l'interface ne correspond pas, on garde la première trouvée
            # avec un fallback sur le choix de la version ip
            if (is_address_version and is_interface_type) or is_address_version or address == None:
                address = interface['ip']

        return address


# Execution
if __name__ == '__main__':
    print OvhPublicCloudInventory()
