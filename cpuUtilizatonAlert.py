#!/usr/bin/env python

import boto3

# session = boto3.Session(profile_name='dv')
ec2 = boto3.resource('ec2')
cloudwatch = boto3.client('cloudwatch')


def get_tag(tagged_object, tag_key):
    """get tag defined by tag_key param for collection(ec2.Instance, ec2.Image etc.)"""
    for tag in tagged_object.tags:
        if tag['Key'] == tag_key:
            return tag['Value']
    return None


def get_instance_names():
    instances = ec2.instances.all()
    inst_names = []
    for instance in instances:
        inst_names.append(get_tag(instance,"Name"))
    return inst_names

def get_instances_id():
    instances = ec2.instances.all()
    inst_ids = []
    for instance in instances:
        inst_ids.append(instance.id)
    return inst_ids


def get_alarms(alarm_type):
    kwargs = {
        'MaxRecords': 100
    }
    al_names = []
    if alarm_type == "cpu":
        while True:
            alarms = cloudwatch.describe_alarms(**kwargs)
            for aln in alarms['MetricAlarms']:
                if "CPU Utilization" in aln['AlarmName']:
                    # print(aln['Dimensions'][0]['Value'])
                    # al_names.append(aln['AlarmName'].replace('CPU Utilization alarm for ', ''))
                    al_names.append(aln['Dimensions'][0]['Value'])
            try:
                kwargs['NextToken'] = alarms['NextToken']
            except KeyError:
                break
    return al_names


def main():
    # variables - alert if not empty:
    # no_cpu_alarm = set(get_instance_names()) - set(get_alarms("cpu"))
    no_cpu_alarm = set(get_instances_id()) - set(get_alarms("cpu"))

    # Nagios check output
    critical_message = "CRITICAL"
    # alert about instances without corresponding alarm
    if bool(no_cpu_alarm):
        critical_message = critical_message + " instances without CPU CloudWatch alarm: " + " ".join(no_cpu_alarm)

    # return check message and status
    if critical_message != "CRITICAL":
        print(critical_message)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()