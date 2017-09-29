#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import datetime

ec2 = boto3.resource('ec2')
retention_days = 2
volume_list=[]
new_volumes_list=[]

for volume in ec2.volumes.filter(Filters=[{'Name': 'tag:lambdaVolumeBackup', 'Values': ['true']}]):
    if volume.tags:
        volume_snapshots=volume.snapshots.all()
        snapshotCount=0
        for snapshot in volume_snapshots:
            if snapshot.description.startswith('lambdaVolumeBackup-'):
                snapshotCount=snapshotCount+1
        if snapshotCount < retention_days:
            if (datetime.datetime.now().replace(tzinfo=None) - volume.create_time.replace(tzinfo=None) < datetime.timedelta(days=retention_days)):
                new_volumes_list.append(volume.id+"("+str(volume.create_time)+")")
            else:
                volume_list.append(volume.id+"("+str(snapshotCount)+")")

if len(volume_list) != 0:
    print "CRITICAL: backup retention problem (<"+str(retention_days)+") or no backup for volume(s): " + ", ".join(volume_list) + " | " + str(len(volume_list))
    exit(2)
else:
    additional_info="new volumes: "+", ".join(new_volumes_list)
    print "OK: "+additional_info+"| 0"
    exit(0)
