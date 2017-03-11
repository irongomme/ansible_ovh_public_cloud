# Ansible OVH Public Cloud dynamic Inventory

Generate simple dynamic inventory against OVH Public Cloud

## Requirements

  - Python dependancies:

```
$ pip install json
$ pip install ovh
```

## How to use

Configuration file must be placed in the script folder

### Configuration file

-> See https://eu.api.ovh.com/createApp/ to get your codes

#### default

  - endpoint : Endpoint code for API host

#### ovh-eu (or your specific code)

  - application_key : your application key
  - application_secret : your application secret
  - consumer_key : your consumer_key

#### openstack

  - openstack_network_default : default network interface type (public or private)
  - openstack_network_ipv6 : preference for ipv6 (yes or no)

### Standalone

```
$ python ./path/to/script/ovh_public_cloud.py
```

### With ansible

```
$ ansible -i ./path/to/script/ovh_public_cloud.py all -m ping
```

## Contributions

Feel free to improve this script to feet your needs !
