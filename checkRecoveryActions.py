#!/usr/bin/env python

import boto3
from sys import exit

"""
Search for instances without 'autorecovery' tag and those with tag but without proper alert action.

LIMITATION: boto3 can featch only 100 alerts without filters. If you have more the 100 please add some sort
of filtering to cloudwatch.describe_alarms()

BLAME: sp0f@sigterm.pl
"""

ec2 = boto3.resource('ec2')
cloudwatch = boto3.client('cloudwatch')

def findInstancesWithoutTag(tagName):
    """"Find instances without tag"""
    instances = ec2.instances.all()

    instancesList = []  # list of instances without backup tag
    for instance in instances:
        # print(instance.id)
        tagFound = False
        try:
            for tag in instance.tags:
                if tag['Key'] == tagName:
                    tagFound = True
        except NoneType:
            instanceList.append(instance.id)
            continue
        if tagFound == False:
            instancesList.append(instance.id)
    return instancesList

def getInstancesWithTagValue(tagName,tagValue="true"):
    """Find instances that have tag `tagName` set to value `tagValue` (default: true)"""

    instances = ec2.instances.filter(Filters=[{"Name": "tag:"+tagName, "Values": [tagValue]}])
    instancesId = []
    for instance in instances:
        #instanceName=getTag(instance,"Name")
        instancesId.append(instance.id)
    return instancesId

def getTag(taggedObject, tagKey):
    """get tag defined by tagKey param for collection(ec2.Instance, ec2.Image etc.)"""
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
    untaggedInstances = findInstancesWithoutTag("autorecovery")
    alarmingInstances = set(taggedInstances)- set(recoveryEnabledInstances)

    # Nagios check output

    criticalMessage="CRITICAL"
    # alert about instances without `recovery` tag
    if len(untaggedInstances) != 0:
        criticalMessage=criticalMessage+" instances without autorecovery tag: "+" ".join(untaggedInstances)

    # alert about instances with `recovery` tag set to `true` without recovery action
    if len(alarmingInstances) != 0:
        criticalMessage=criticalMessage+" instances without autorecovery action: "+" ".join(alarmingInstances)

    # return check message and status
    if criticalMessage != "CRITICAL":
        print criticalMessage
        exit(2)
    else:
        print "OK"
        exit(0)


if __name__ == '__main__':
    main()
