#!/usr/bin/env python
# -*- coding: utf-8 -*-

#ANSIBLE_METADATA = {'metadata_version': '1.0', 'status': ['preview'], 'supported_by': 'community'}
from __future__ import absolute_import, division, print_function
__metaclass__ = type



DOCUMENTATION = '''
---
module: ovh_dns
author: "Mathieu \"ralmn\" HIREL"
short_description: "Manage OVH DNS"
description:
    - Manage OVH DNS
requirements:
    - ovh >  0.3.5
options:
    domain:
        required: true
        description: domain
    entries:
        required: true
        description: entry or ips
    state:
        required: false
        default : present
        choises: ['present', 'delete'] 
        description: domain would be present or delete
    type:
        required: false
        default: A
        choices: ['A', 'AAAA', 'CNAME']
        description:
          - Type of DNS record (A, AAAA, CNAME)
    endpoint:
        required: true
        description:
            - The endpoint to use ( for instance ovh-eu)
    application_key:
        required: true
        description:
            - The applicationKey to use
    application_secret:
        required: true
        description:
            - The application secret to use
    consumer_key:
        required: true
        description:
            - The consumer key to use

'''

EXAMPLES = '''

ovh_dns:
    domain: "{{ ansible_hostname }}.{{ base_domain }}"
    entries:
      - "{{ ip|default(ansible_default_ipv4['address']) }}"
    endpoint: "{{ovh_endpoint}}"
    application_key: "{{ovh_application_key}}"
    application_secret: "{{ovh_application_secret}}"
    consumer_key: "{{ovh_consumer_key}}"
    state: overwrite

'''

import sys, os

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule


def getOvhClient(ansibleModule):
    endpoint = ansibleModule.params.get('endpoint')
    application_key = ansibleModule.params.get('application_key')
    application_secret = ansibleModule.params.get('application_secret')
    consumer_key = ansibleModule.params.get('consumer_key')

    return ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )


def get_real_base_domain(domain):
    if domain[-1] == ".":
        domain = domain[:-1]
    return  ".".join(domain.split(".")[-2:])

def get_sub_domain(domain):
    if domain[-1] == ".":
        domain = domain[:-1]
    return  ".".join(domain.split(".")[:-2])

def sameEntry(record1, record2):
    return record1['target'] == record2['target'] and record1['fieldType'] == record2['fieldType']

def createRecord(domain, subDomain, record, ovhClient):
    #print(record)
    #print(dict(fieldType=record['fieldType'], target=record['target'], subDomain=subDomain))
    ovhClient.post('/domain/zone/{}/record'.format(domain), fieldType=record['fieldType'], target=record['target'], subDomain=subDomain)
    

def deleteRecord(domain, rid, ovhClient):
    print('delete', '/domain/zone/{}/record/{}'.format(domain, rid))
    ovhClient.delete('/domain/zone/{}/record/{}'.format(domain, rid))


def main():
    module = AnsibleModule(
        argument_spec = dict(
            domain = dict(required=True),
            entries = dict(required=True, type='list'),
            state =  dict(default='present', choices=['present', 'delete', 'overwrite']),
            type = dict(default='A', choices=['A', 'AAAA']),
            endpoint = dict(required=True),
            application_key = dict(required=True, no_log=True),
            application_secret = dict(required=True, no_log=True),
            consumer_key=  dict(required=True, no_log=True)
        )
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh-api python module is required to run this module ')

    domain = module.params.get('domain')
    entries = module.params.get('entries')
    dnsType = module.params.get('type')
    state = module.params.get('state')

    real_base_domain = get_real_base_domain(domain) 
    subdomain = get_sub_domain(domain)

    ovhClient = getOvhClient(module)

    result = {"changed":False}

    try:
        zones = ovhClient.get('/domain/zone')
    except APIError as error:
        module.fail_json(msg="Your are not allowed to list domain zone", **result)

    if real_base_domain not in zones: 
        module.fail_json(msg='Your are not allowed to controlled domain {} ( allowed zone : {} )'.format(real_base_domain, ', '.join(zones)), **result)

    #print("Setup domain={}, subdomain={}, entries={}, type={}".format(real_base_domain, subdomain, str(entries), dnsType))

    recordsIds = ovhClient.get('/domain/zone/{}/record'.format(real_base_domain), subDomain=subdomain)

    records = []    

    for rid in recordsIds:
        record = ovhClient.get('/domain/zone/{}/record/{}'.format(real_base_domain, rid))
        records.append({'id': rid, 'target': record['target'], 'fieldType': record['fieldType'], 'created': True})

    plannedRecords = []

    for entry in entries:
        plannedRecords.append({'id': None, 'target': entry, 'fieldType': dnsType, 'created': False})

    if state == 'present':
        for record in plannedRecords:
            if bool([r for r in records if sameEntry(record, r) ]):
                continue
            try:   
                createRecord(real_base_domain, subdomain, record, ovhClient)
            except APIError as error:
                print(error, file=sys.stdout)
                module.fail_json(msg="Failed to create record... {} {}".format(entries, type(entries)))
            result['changed'] = True
    elif state == 'overwrite':
        for record in records:

            planned = [r for r in plannedRecords if sameEntry(record, r)]
            if bool(planned):
                for p in planned:
                    p['created'] = True
            else:
                deleteRecord(real_base_domain, record['id'], ovhClient)
                result['changed'] = True
        for record in plannedRecords:
            if not record['created']:
                createRecord(real_base_domain, subdomain, record, ovhClient)
                result['changed'] = True
    elif state == 'delete' :
        for record in plannedRecords:
            realRecord = [r for r in records if (sameEntry(record, r))]
            #print(realRecord)
            for r in realRecord:
                try:  
                    deleteRecord(real_base_domain, r['id'], ovhClient)
                except APIError as error:
                    #print(error, file=sys.stdout)
                    module.fail_json(msg="Failed to delte record... {} {}".format(real_base_domain,r['id']))
                result['changed'] = True

    module.exit_json(message=str(module), **result)

from ansible.module_utils.basic import *  # noqa
if __name__ == '__main__':
    main()
