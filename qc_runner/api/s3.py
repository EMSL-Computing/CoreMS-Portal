import boto3
from botocore.client import Config
from s3path import PureS3Path, register_configuration_parameter
import os
from minio import Minio
from api import config 

def s3_init():

    minio_bucket_path = PureS3Path('/')
    s3 = boto3.resource(
                's3',
                endpoint_url=config.MINIO_URL,
                aws_access_key_id=config.MINIO_ROOT_USER,
                aws_secret_access_key=config.MINIO_ROOT_PASSWORD,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1')

    register_configuration_parameter(minio_bucket_path, resource=s3)
    return s3

def minio_init():

    minio = Minio(
            config.MINIO_URL.replace('http://', ''),
            access_key=config.MINIO_ROOT_USER,
            secret_key=config.MINIO_ROOT_PASSWORD,
            secure=False
                )

    return minio

def check_create_buckets(minio, buckets_list):

    buckets = ['fticr-data', 'gcms-data']
    for bucket in buckets:
        if not minio.bucket_exists(bucket):
            minio.make_bucket(bucket)
