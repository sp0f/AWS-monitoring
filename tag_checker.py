#!/usr/bin/python
# coding: utf-8

from sys import exit
import boto3

ec2 = boto3.resource('ec2')
required_tags = ("backup", "autorecovery", "Patch Group")


def find_untagged_instances(instance_tag):
    """Find instances without backup tag."""
    instances = ec2.instances.all()

    instancesList = []  # list of instances without backup tag
    for instance in instances:
        configured = False
        for tag in instance.tags:
            if tag['Key'] == instance_tag:
                configured = True
        if configured is False:
            instancesList.append(instance)
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
