#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
from datetime import datetime, timedelta

ec2 = boto3.client('ec2')

def find_old_images(too_old):
    old_images=[]
    all_images=ec2.describe_images(
        Owners=['self']
    )['Images']

    for image in all_images:
        creation_date = datetime.strptime(image['CreationDate'], "%Y-%m-%dT%H:%M:%S.000Z")

        if creation_date < datetime.now()-too_old:
            # exclude images with tag 'archive' set to anything
            if 'Tags' in image.keys():
                archive=False
                for tag in image['Tags']:
                    if tag['Key'] == 'archive':
                        archive=True
                if not archive:
                    old_images.append(image['ImageId'])
            else:
                old_images.append(image['ImageId'])




    return old_images


def main():
    too_old=timedelta(days=16)
    old_images=find_old_images(too_old)

    # Nagios check output
    criticalMessage = "CRITICAL"

    # alert about unencrypted volumes
    if len(old_images) != 0:
        criticalMessage = criticalMessage + " old machine images: " + " ".join(old_images) +" | "+str(len(old_images))

    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()