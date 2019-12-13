#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import re
from datetime import datetime, timedelta

region_name = 'eu-west-1' # AWS region
ec2 = boto3.client('ec2', region_name=region_name)

max_age=180 # in days
required_tags = {
    'issueID': re.compile(".*"),
    'expireDate': re.compile("\d\d-\d\d-\d\d\d\d"),
    'comment': re.compile(".+")
}


exclude_tags = ['srcInstanceId'] # srcInstanceId is a tag that identified our backup system images

ami_missing_tags={} # ami with missig tag, format: { 'ami_id' : [ 'tag_list',] }
ami_wrong_tag = {} # ami with incorrect tag values, format { 'ami_id' : [ 'tag_list',] }
ami_expired = [] # expired ami list


def get_tag(tagged_object, tag_key):
    """get tag defined by tag_key param for collection(ec2.Instance, ec2.Image etc.)"""
    if 'Tags' in tagged_object:
        for tag in tagged_object['Tags']:
            if tag['Key'] == tag_key:
                return tag['Value']
    return None


def find_naughty_ami(ami_list):
    """ check if image is compliant with our standard:
        * some images are excluded because they are part of backup process
        * image need to have some tags (required_tags,keys)
        * image need to have task in proper form (required_tags.values() - regexp patterns)
        * image expiration date need to be < today()
    """
    for ami in ami_list:
        skip=False
        for tag in exclude_tags:
            if (get_tag(ami, tag) is not None):
                skip=True
        if (not skip):
            # print("ami: "+ami['ImageId'])
            for tag in required_tags.keys():
                tag_value = get_tag(ami, tag)
                if (tag_value == None):
                    if ami['ImageId'] in ami_missing_tags:
                        ami_missing_tags[ami['ImageId']].append(tag)
                    else:
                        ami_missing_tags[ami['ImageId']] = [tag,]
                    # ami_missing_tags.append(ami['ImageId'])
                    continue
                elif (not required_tags[tag].fullmatch(tag_value)):
                    if ami['ImageId'] in ami_wrong_tag:
                        ami_wrong_tag[ami['ImageId']].append(tag)
                    else:
                        ami_wrong_tag[ami['ImageId']] = [tag,]
                    # ami_wrong_tag.append(ami['ImageId'])
                elif (tag == 'expireDate'):
                    expire_datetime=datetime.strptime(tag_value, "%d-%m-%Y")
                    if(expire_datetime <= datetime.today()):
                        ami_expired.append(ami['ImageId'])
                    if(expire_datetime >= (datetime.today()+timedelta(days=max_age))):
                        if ami['ImageId'] in ami_wrong_tag:
                            ami_wrong_tag[ami['ImageId']].append(tag)
                        else:
                            ami_wrong_tag[ami['ImageId']] = [tag, ]


def main():
    all_our_amis=ec2.describe_images(
        Owners=['self'],
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }
        ]
    )['Images']

    find_naughty_ami(all_our_amis)

    criticalMessage = "CRITICAL"

    if(ami_missing_tags):
        criticalMessage += " missig required tags: "
        for ami in ami_missing_tags:
            criticalMessage += ami+"("
            criticalMessage += ' '.join(ami_missing_tags[ami])
            criticalMessage +=") "
    if(ami_wrong_tag):
        criticalMessage += " wrong tag value or expireDate > "+str(max_age)+" : "
        for ami in ami_wrong_tag:
            criticalMessage += ami+"("
            criticalMessage += ' '.join(ami_wrong_tag[ami])
            criticalMessage +=") "
    if(ami_expired):
        criticalMessage += " expired images: "
        criticalMessage += ' '.join(ami_expired)

    # print(criticalMessage)

    # return check message and status
    if criticalMessage != "CRITICAL":
        print(criticalMessage)
        exit(2)
    else:
        print("OK")
        exit(0)


if __name__ == '__main__':
    main()
