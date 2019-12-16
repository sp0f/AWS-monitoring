#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import re
from sys import exit
from datetime import datetime, timedelta

owner_id = '260187409195'
ec2 = boto3.client('ec2')
max_age = 180 # days

def all_ami_snapshots():
    """Return list of all snapshots ids related to AMI"""
    all_ami_snapshots = ec2.describe_snapshots(
        Filters=[
            {
                'Name': 'status',
                'Values': ['completed']
            },
            {
                'Name': 'description',
                'Values': ['Created by CreateImage*','Copied for DestinationAmi*']
            }
        ],
        OwnerIds=[owner_id,]
    )['Snapshots']

    return all_ami_snapshots

def abandoned_snapshots_list(all_ami_snapshots):
    """Return list of all snapshots ids related to EXISTING AMI"""

    amis = ec2.describe_images(
        Owners = [owner_id,]
    )['Images']

    abandoned_snapshots=[]

    for snap in all_ami_snapshots:
        snap_is_abandoned = True
        for ami in amis:
            if ami['ImageId'] in snap['Description']:
                snap_is_abandoned = False
        if snap_is_abandoned:
            abandoned_snapshots.append(snap['SnapshotId'])

    return abandoned_snapshots

def find_untaged_snapshots(tagKey,snapshot_ids):
    """Return list of untagged snapshots"""

    untagged_snapshots = []
    snapshots = ec2.describe_snapshots(
        SnapshotIds=snapshot_ids
    )['Snapshots']

    for snap in snapshots:
        no_tag = True

        if 'Tags' in snap:
            for tag in snap['Tags']:
                if tag['Key'] == tagKey:
                    no_tag = False
        if no_tag:
            untagged_snapshots.append(snap['SnapshotId'])
    return untagged_snapshots

def verify_expire_tag(snapshot_ids, tag_key):
    expired_snapshots=[]
    snapshots = ec2.describe_snapshots(SnapshotIds=snapshot_ids)['Snapshots']
    expire_date_format = re.compile("\d\d-\d\d-\d\d\d\d")

    for snap in snapshots:
        no_tag = True
        if 'Tags' in snap:
            for tag in snap['Tags']:
                if tag['Key'] == tag_key:
                    if (not expire_date_format.fullmatch(tag['Value'])):
                        expire_date_format.append(snap['SnapshotId'])
                    expire_datetime = datetime.strptime(tag['Value'], "%d-%m-%Y")
                    if (expire_datetime <= datetime.today()):
                        expired_snapshots.append(snap['SnapshotId'])
                    if (expire_datetime >= (datetime.today() + timedelta(days=max_age))):
                        expired_snapshots.append((snap['SnapshotId']))
                    else:
                        no_tag = False
        if no_tag:
            expired_snapshots.append(snap['SnapshotId'])

    return expired_snapshots


def find_unencrypted_snapshots(snapshot_ids):
    unencrypted_snapshots=[]
    snapshots = ec2.describe_snapshots(SnapshotIds=snapshot_ids)['Snapshots']

    for snap in snapshots:
        if snap['Encrypted'] is False:
            unencrypted_snapshots.append(snap['SnapshotId'])
    return unencrypted_snapshots



def main():
    ami_snapshots = all_ami_snapshots()
    all_snapshots = ec2.describe_snapshots(
        Filters=[
            {
                'Name': 'status',
                'Values': ['completed']
            }
        ],
        OwnerIds=[owner_id, ]
    )['Snapshots']
    ami_snapshots_ids = []
    all_snapshots_ids = []

    for ami in ami_snapshots:
        ami_snapshots_ids.append(ami['SnapshotId'])

    for ami in all_snapshots:
        all_snapshots_ids.append(ami['SnapshotId'])

    abandoned_snapshots = abandoned_snapshots_list(ami_snapshots)

    # dirty magic, dirty tricks
    non_ami_snapshots = list(set(all_snapshots_ids)-set(ami_snapshots_ids))
    # untagged_snapshots = find_untaged_snapshots('archive',non_ami_snapshots)
    expired_snapshots = verify_expire_tag(non_ami_snapshots,'expireDate')
    unencrypted_snapshots = find_unencrypted_snapshots(non_ami_snapshots)


    # Nagios check output
    criticalMessage = "CRITICAL"
    # alert about abandoned ami snapshots
    if len(abandoned_snapshots) != 0:
        criticalMessage = criticalMessage + " abandoned AMI snapshots: " + " ".join(abandoned_snapshots)

    # alert about untaged snapshots (non ami snapshots)
    if len(expired_snapshots) != 0:
        criticalMessage = criticalMessage + " expired (expireDate < now()+"+str(max_age)+" or wrongly tagged snapshots: " + " ".join(expired_snapshots)

    if len(unencrypted_snapshots) != 0:
        criticalMessage = criticalMessage + " unencrypted snapshots: " + " ".join(unencrypted_snapshots)
    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()
