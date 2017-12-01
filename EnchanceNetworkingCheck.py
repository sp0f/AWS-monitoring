#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import os.path

ec2 = boto3.resource('ec2')

def getTag(taggedObject, tagKey):
    """get tag defined by tagKey param for collection(ec2.Instance, ec2.Image etc.)"""
    for tag in taggedObject.tags:
        if tag['Key'] == tagKey:
            return tag['Value']
    return None

ena_instance_list=[]
vf_instance_list=[]
exclude_list=[]
exclude_file="exclude_list.txt"

if os.path.isfile(exclude_file):
    with  open(exclude_file, 'r') as f:
        for line in f:
            exclude_list.append(f.readline())

# print("\nVF\n")
instances = ec2.instances.filter(
    Filters=[
        {
            'Name': 'instance-type',
            'Values': [
                'c3.large', 'c3.xlarge', 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge',
                'c4.large', 'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge', 'c4.8xlarge',
                'r3.large', 'r3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge',
                'm4.large', 'm4.xlarge', 'm4.2xlarge', 'm4.4xlarge', 'r4.10xlarge',
                'd2.xlarge', 'd2.2xlarge', 'd2.4xlarge', 'd2.8xlarge',
                'i2.large', 'i2.xlarge', 'i2.2xlarge', 'i2.4xlarge', 'i2.8xlarge',
            ]
        },
    ],
    DryRun=False,
    MaxResults=200,
)

for instance in instances:

    sriovNetSupport=instance.describe_attribute(
        Attribute="sriovNetSupport",
        DryRun=False
    )
    if not sriovNetSupport['SriovNetSupport']:
        vf_instance_list.append(instance.id+" "+getTag(instance,"Name"))
        # print(getTag(instance,"Name")+" "+instance.id+" "+instance.instance_type)


# print("\nENA\n")

instances = ec2.instances.filter(
    Filters=[
        {
            'Name': 'instance-type',
            'Values': [
                'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge','c5.18xlarge',
                'r4.large', 'r4.xlarge', 'r4.2xlarge', 'r4.4xlarge', 'r4.8xlarge',
                'f1.2xlarge','f1.16xlarge',
                'g3.4xlarge','g3.8xlarge','g3.16xlarge',
                'i3.large', 'i3.xlarge', 'i3.2xlarge', 'i3.4xlarge', 'i3.8xlarge','i3.16xlarge',
                'p2.xlarge','p2.8xlarge','p2.16xlarge',
                'p3.xlarge','p3.8xlarge','p3.16xlarge',
                'x1.32xlarge','x1.16xlarge'

            ]
        },
    ],
    DryRun=False,
    MaxResults=200,
)

for instance in instances:
    if not instance.ena_support:
        ena_instance_list.append(instance.id+" "+getTag(instance,"Name"))
        # print(getTag(instance,"Name")+" "+instance.id+" "+instance.instance_type)

if ( (len(vf_instance_list) != 0) or (len(ena_instance_list) != 0)):
    print("CRITICAL: instances without ENA ("+" ,".join(ena_instance_list)+") VF ("+" ,".join(vf_instance_list))
    exit(2)
else:
    print("OK")
    exit(0)