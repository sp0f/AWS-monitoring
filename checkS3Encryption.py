#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import botocore
from sys import exit
import os.path

s3 = boto3.resource('s3')
s3client = boto3.client('s3')

buckets = s3.buckets.all()
unencrypted_bucket_list= []

exclude_list=[]
exclude_file="s3Encryption-exclude_list.txt"

if os.path.isfile(exclude_file):
    with  open(exclude_file, 'r') as f:
        while True:
            line=f.readline()
            if not line:
                break
            else:
                exclude_list.append(line.rstrip())


# print(exclude_list)

for bucket in buckets:
    if bucket.name in exclude_list:
        continue
    try:
        response=s3client.get_bucket_encryption(
            Bucket=bucket.name
        )
    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == "NoSuchBucket":
            continue
        if err.response['Error']['Code'] == "ServerSideEncryptionConfigurationNotFoundError":
            # print(bucket.name)
            #if bucket.name not in exclude_list:
            unencrypted_bucket_list.append(bucket.name)
        else:
            raise err

if len(unencrypted_bucket_list) != 0:
    print("CRITICAL - unencrypted buckets: "+" ".join(unencrypted_bucket_list))
    exit(2)
else:
    print("OK - all buckets set with default encryption (excluded: "+" ".join(exclude_list)+")")
    exit(0)
