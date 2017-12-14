#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import botocore
from sys import exit

s3 = boto3.resource('s3')
s3client = boto3.client('s3')

buckets = s3.buckets.all()
unencrypted_bucket_list= []

for bucket in buckets:
    try:
        response=s3client.get_bucket_encryption(
            Bucket=bucket.name
        )
    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == "ServerSideEncryptionConfigurationNotFoundError":
            # print(bucket.name)
            unencrypted_bucket_list.append(bucket.name)

if len(unencrypted_bucket_list) != 0:
    print("CRITICAL - unencrypted buckets: "+" ".join(unencrypted_bucket_list))
    exit(2)
else:
    print("OK - all buckets set with default encryption")
    exit(0)
