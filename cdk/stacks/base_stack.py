import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # --- Context or environment variables ---
        env_name = self.node.try_get_context("env") or os.getenv("ENV_NAME", "dev")
        region = self.region
        account = self.account

        main_bucket_name = (
            self.node.try_get_context("main_bucket_name")
            or os.getenv("MAIN_BUCKET_NAME", f"{env_name}-main-bucket-{account}")
        )

        log_bucket_name = (
            self.node.try_get_context("log_bucket_name")
            or os.getenv("LOG_BUCKET_NAME", f"{env_name}-log-bucket-{account}")
        )

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
            removal_policy=s3.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        log_bucket = s3.Bucket(
            self,
            "LogBucket",
            bucket_name=log_bucket_name,
            versioned=False,
            removal_policy=s3.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # 2. VPC (isolated subnets, 1 NAT gateway defaul