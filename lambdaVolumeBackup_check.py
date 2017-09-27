import boto3

ec2 = boto3.resource('ec2')
retention_days = 2
volume_list=[]

for volume in ec2.volumes.filter(Filters=[{'Name': 'tag:lambdaVolumeBackup', 'Values': ['true']}]):
    if volume.tags:
        volume_snapshots=volume.snapshots.all()
        snapshotCount=0
        for snapshot in volume_snapshots:
            if snapshot.description.startswith('lambdaVolumeBackup-'):
                snapshotCount=snapshotCount+1
                #print snapshot.id+"("+str(snapshotCount)+")"
        if snapshotCount < retention_days:
                    volume_list.append(volume.id+"("+str(snapshotCount)+")")

if len(volume_list) != 0:
    print "CRITICAL backup retention problem (<"+str(retention_days)+") or no backup for volume(s): " + ", ".join(volume_list) + " | " + str(len(volume_list))
    exit(2)
else:
    print "OK | 0"
    exit(0)
