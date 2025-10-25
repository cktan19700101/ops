import os
from aws_cdk import (
    Stack,
    RemovalPolicy,  # ← add this
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct
import boto3

class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # --- Context or environment variables ---
        env_name = self.node.try_get_context("env") or os.getenv("ENV_NAME", "dev")
        account = os.getenv("CDK_DEFAULT_ACCOUNT") or boto3.client("sts").get_caller_identity()["Account"]
        region = os.getenv("CDK_DEFAULT_REGION") or 'ap-southeast-1'

        main_bucket_name = f"{env_name}-main-bucket-{account}"

        log_bucket_name = f"{env_name}-log-bucket-{account}"

        instance_type_str = (
            self.node.try_get_context("instance_type")
            or os.getenv("INSTANCE_TYPE", "t3.xlarge")
        )

        nat_gateways = int(
            self.node.try_get_context("nat_gateways") or os.getenv("NAT_GATEWAYS", "1")
        )

        # --- Resources ---
        # 1. Buckets
        main_bucket = s3.Bucket(
            self,
            "MainBucket",
            bucket_name=main_bucket_name,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        log_bucket = s3.Bucket(
            self,
            "LogBucket",
            bucket_name=log_bucket_name,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )