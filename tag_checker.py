#!/usr/bin/python
# coding: utf-8

"""Compliance check. Search for instances without required tagKey."""
from sys import exit
import boto3


aws_region = 'eu-west-1'
aws_profile = 'default'

required_tags = ("backup", "autorecovery", "Patch Group")

session = boto3.Session(region_name=aws_region, profile_name=aws_profile)
ec2 = session.resource('ec2')


def find_untagged_instances(instance_tag):
    """Find instances without backup tag."""
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'instance-state-name',
            'Values': ['pending', 'running', 'shutting-down', 'stopping', 'stopped']
        }
    ])

    instancesList = []  # list of instances without backup tag
    for instance in instances:
        configured = False
        if instance.tags:
            for tag in instance.tags:
                if tag['Key'] == instance_tag:
                    configured = True
            if configured is False:
                instancesList.append(instance)
        else:
            instancesList.apppend(instance)
    return instancesList


def getTag(taggedObject, tagKey):
    """Get tag defined by tagKey for iterator taggedObject."""
    for tag in taggedObject.tags:
        if tag['Key'] == tagKey:
            return tag['Value']
    return None


if __name__ == '__main__':
    naughty_instances = []

    for tag in required_tags:
        instances = find_untagged_instances(tag)
        for instance in instances:
            instance_name = getTag(instance, 'Name')
            if instance_name is None:
                instance_name = instance.id
            naughty_instances.append(instance_name+"[tag:"+tag+"]")

    if len(naughty_instances) != 0:
        print("CRITICAL instance(s) without required tags: " +
              " ".join(naughty_instances) +
              " | " + str(len(naughty_instances)))
        exit(2)
    else:
        print("OK | 0")
        exit(0)
