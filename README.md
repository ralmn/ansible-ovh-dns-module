# ansible-ovh-dns-module
Module for setup OVH DNS with Ansible

Created by [Mathieu "ralmn" HIREL](https:://twitter.com/ralmn45)

# Requirement 

* OVH python module
	`pip install ovh`
* Ansible 2.0+
# Installation

1. Copy this module (`ovh_dns.py`) in your library directory or use `-M /path/to/module/ovh_dns`
2. Create application token for OVH api : https://api.ovh.com/g934.first_step_with_api
3. Save your `endpoint`, `application_key`, `application_secret` and `consumer_key` in your playbook (in inventory vars for exemple) 
# Usage


## Options

**domain**  (string): full domain to setup (exemple: node-1.exemple.com)
**entries** (list): ips or domain to save for the domain
**type** (string): Type of dns field, allowed : A, AAAA or CNAME
**state** (string): 
* *present* : Add new entries only. No delete other entry
* *delete*: remove entries
* *overwrite*: delete unsed entry and create new
**endpoint** (string): OVH API endpoint
**application_key, application_secret, consumer_key** (strings): OVH API tokens

## Exemple 

```yaml
name: 'DNS | Test | Setup Domain'
  ovh_dns:
    domain: "{{ ansible_hostname }}.{{ base_domain }}"
    entries:
      - "{{ ip|default(ansible_default_ipv4['address']) }}"
    endpoint: "{{ovh_endpoint}}"
    application_key: "{{ovh_application_key}}"
    application_secret: "{{ovh_application_secret}}"
    consumer_key: "{{ovh_consumer_key}}"
    state: 'overwrite'
```