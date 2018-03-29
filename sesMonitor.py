#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime, timezone

ses_client = boto3.client('ses');

bounced = 0
complaints = 0
send_24h = 0
max24h_send=0

BOUNCED_MAX = 10 # per 1h
COMPLAINTS_MAX = 1 # per 1h
QUOTA_USAGE_MAX = 70 # % per 24h

# get current quota
try:
    quota = ses_client.get_send_quota()
except ClientError as e:
    print(e.response['Error']['Message'])
    exit(1)
else:
    max24h_send=quota['Max24HourSend']



# get statistics
try:
    response = ses_client.get_send_statistics()
except ClientError as e:
    print(e.response['Error']['Message'])
    exit(1)
else:
    now = datetime.now(timezone.utc)

    for sample in response['SendDataPoints']:
       time_delta=now - sample['Timestamp']
       if time_delta.total_seconds() <= (3600*24): # last 24h
           send_24h = send_24h + sample['DeliveryAttempts']
       if time_delta.total_seconds() <= 3600:
           # print(sample)
           bounced=bounced + sample['Bounces']
           complaints= complaints + sample['Complaints']
           # send_1h=send_1h+sample['DeliveryAttempts']


quota_used_percent= send_24h / max24h_send * 100

if (complaints > COMPLAINTS_MAX) or (bounced > BOUNCED_MAX) or (quota_used_percent > QUOTA_USAGE_MAX):
    critical_message = "CRITICAL: " \
        + "complaints: " + str(complaints) + " (max: " + str(COMPLAINTS_MAX) + "), " \
        + "bounces: " + str(bounced) + " (max: " + str(BOUNCED_MAX) + "), " \
        + "quota used: " + str(quota_used_percent) + "% (max: " + str(QUOTA_USAGE_MAX) + "%)" \
        + "|complaints="+str(complaints)+", bounces="+str(bounced)+", quota_used_percentage="+str(quota_used_percent)[:5]
    print(critical_message)
    exit(2)
else:
    ok_message = "OK: " \
        + "complaints: " + str(complaints) + " (max: " + str(COMPLAINTS_MAX) + "), " \
        + "bounces: " + str(bounced) + " (max: " + str(BOUNCED_MAX) + "), " \
        + "quota used: " + str(quota_used_percent)[:5] + "% (max: " + str(QUOTA_USAGE_MAX) + "%)" \
        + "|complaints="+str(complaints)+", bounces="+str(bounced)+", quota_used_percentage="+str(quota_used_percent)[:5]
    print(ok_message)

