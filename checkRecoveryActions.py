#!/usr/bin/env python
# coding: utf-8

import boto3
from sys import exit

"""Search for instances without configured auto recovery action."""

aws_region = 'eu-west-1'
# aws_profile = 'default'

session = boto3.Session(region_name=aws_region)
ec2 = session.resource('ec2')
cloudwatch = session.client('cloudwatch')

def getInstancesWithTagValue(tagName,tagValue="true"):
    """Find instances that have tag `tagName` set to value `tagValue` (default: true)."""

    instances = ec2.instances.filter(Filters=[{"Name": "tag:"+tagName, "Values": [tagValue]}])
    instancesId = []
    for instance in instances:
        instancesId.append(instance.id)
    return instancesId


def getTag(taggedObject, tagKey):
    """Get tag defined by tagKey param for collection(ec2.Instance, ec2.Image etc.)."""
    for tag in taggedObject.tags:
        if tag['Key'] == tagKey:
            return tag['Value']
    return None

def main():
    kwargs = {
        'MaxRecords': 100
    }
    recoveryEnabledInstances=[]

    while True:
        alarmList = cloudwatch.describe_alarms(**kwargs)

        for alarm in alarmList['MetricAlarms']:
            # print(alarm)
            if len(alarm['Dimensions']) != 0 and 'arn:aws:automate:eu-west-1:ec2:recover' in alarm['AlarmActions']:
                recoveryEnabledInstances.append(alarm['Dimensions'][0]['Value'])
        try:
            kwargs['NextToken'] = alarmList['NextToken']
        except KeyError:
            break

    taggedInstances = getInstancesWithTagValue("autorecovery","true")
    alarmingInstances = set(taggedInstances)- set(recoveryEnabledInstances)

    # Nagios check output
    criticalMessage="CRITICAL"

    # alert about instances with `recovery` tag set to `true` without recovery action
    if len(alarmingInstances) != 0:
        criticalMessage=criticalMessage+" instances without autorecovery action: "+" ".join(alarmingInstances)

    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()
