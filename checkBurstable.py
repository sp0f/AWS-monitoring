#!/usr/bin/env python3
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')


paginator = cloudwatch.get_paginator('list_metrics')

def check_burstable_metric(dimension, metric_name, namespace, check_period=30, balance_alert_level=0):
    problematic_instances = []
    for response in paginator.paginate(
            Dimensions=[{'Name': dimension}],
            MetricName=metric_name,
            Namespace=namespace
            ):
        for metric in (response['Metrics']):
            # print(metric)
            statistic = cloudwatch.get_metric_statistics(
                Namespace=metric['Namespace'],
                Dimensions=metric['Dimensions'],
                MetricName=metric['MetricName'],
                StartTime=datetime.utcnow() - timedelta(minutes=check_period),
                EndTime=datetime.utcnow(),
                Statistics=['Average'],
                Period=check_period*60
            )
            # print(statistic)
            if (len(statistic['Datapoints']) > 0):
                if (statistic['Datapoints'][0]['Average'] <= balance_alert_level):
                    problematic_instances.append(metric['Dimensions'][0]['Value'])
    return problematic_instances

def main():
    # print(check_burstable_metric('InstanceId', 'CPUCreditBalance', 'AWS/EC2'))
    # print(check_burstable_metric('VolumeId', 'BurstBalance', 'AWS/EBS',balance_alert_level=99))

    criticalMessage = "CRITICAL"
    cpu_constrained_instances=check_burstable_metric('InstanceId', 'CPUCreditBalance', 'AWS/EC2')
    io_constrained_volumes=check_burstable_metric('VolumeId', 'BurstBalance', 'AWS/EBS')

    if len(cpu_constrained_instances) != 0:
        criticalMessage=criticalMessage+" instances with CPU utilization problems: "+" ".join(cpu_constrained_instances)
    if len(io_constrained_volumes) != 0:
        criticalMessage=criticalMessage+" volumes with IO utilization problems: "+" ".join(io_constrained_volumes)

    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()
