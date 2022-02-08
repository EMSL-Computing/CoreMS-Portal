import boto3
from botocore.client import Config
from s3path import PureS3Path, register_configuration_parameter
import os
from minio import Minio

def s3_init():

    minio_bucket_path = PureS3Path('/')
    s3 = boto3.resource(
                's3',
                endpoint_url=os.environ.get("MINIO_URL", 'http://localhost:9000'),
                aws_access_key_id=os.environ.get("MINIO_ROOT_USER"),
                aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD"),
                config=Config(signature_version='s3v4'),
                region_name='us-east-1')

    register_configuration_parameter(minio_bucket_path, resource=s3)

    s3_client = boto3.client(
                's3',
                endpoint_url=os.environ.get("MINIO_URL", 'http://localhost:9000'),
                aws_access_key_id=os.environ.get("MINIO_ROOT_USER"),
                aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD"),
                config=Config(signature_version='s3v4'),
                region_name='us-east-1')

    register_configuration_parameter(minio_bucket_path, resource=s3)

    return s3, s3_client

def minio_init():

    minio = Minio(
            os.environ.get("MINIO_URL", 'localhost:9000').replace('http://', ''),
            access_key=os.environ.get("MINIO_ROOT_USER"),
            secret_key=os.environ.get("MINIO_ROOT_PASSWORD"),
            secure=False
                )

    return minio

def check_create_buckets(minio, buckets_list):

    buckets = ['fticr-data', 'gcms-data']
    for bucket in buckets:
        if not minio.bucket_exists(bucket):
            minio.make_bucket(bucket)
