#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
from sys import exit
import os.path

exclude_file_path="ebs_exclude_list.txt"
ec2 = boto3.client('ec2')

def find_unencrypted_volumes(exclude_list=None):
    bad_volume_list=[]

    unencrypted_volume_list=ec2.describe_volumes(
        Filters=[
            {
                'Name': 'encrypted',
                'Values': [ 'false' ]
            }
        ]
    )['Volumes']

    # if exclude list provided and it's not a empty list
    if exclude_list:
        for volume in unencrypted_volume_list:
            if volume['VolumeId'] not in exclude_list:
                bad_volume_list.append(volume['VolumeId'])
    else:
        for volume in unencrypted_volume_list:
            bad_volume_list.append(volume['VolumeId'])

    return bad_volume_list


def get_exclude_list(exclude_file):
    exclude_list=[]
    if os.path.isfile(exclude_file):
        with  open(exclude_file, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                else:
                    exclude_list.append(line.rstrip())
    return exclude_list


def main():
    exclude_list= get_exclude_list(exclude_file_path)
    unencrypted_volumes=find_unencrypted_volumes(exclude_list)

    # Nagios check output
    criticalMessage = "CRITICAL"

    # alert about unencrypted volumes
    if len(unencrypted_volumes) != 0:
        criticalMessage = criticalMessage + " unencrypted EBS volumes: " + " ".join(unencrypted_volumes)

    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()