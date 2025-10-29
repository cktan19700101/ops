import os
import boto3
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,
    Tags,
)
from constructs import Construct
from aws_cdk import CfnOutput

class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # --- Context or environment variables ---
        env_name = self.node.try_get_context("env") or os.getenv("ENV_NAME", "dev")
        account = os.getenv("CDK_DEFAULT_ACCOUNT") or boto3.client("sts").get_caller_identity()["Account"]
        region = os.getenv("CDK_DEFAULT_REGION") or "ap-southeast-1"

        main_bucket_name = f"{env_name}-main-bucket-{account}"
        log_bucket_name = f"{env_name}-log-bucket-{account}"

        nat_gateways = int(
            self.node.try_get_context("nat_gateways") or os.getenv("NAT_GATEWAYS", "0")
        )

        # --- 1. VPC (for Batch, API Gateway, EC2) ---
        # Public for internet-facing (e.g., NAT, ALB)
        # Private for app compute (EC2, Batch)
        # Isolated for data or Lambda (no internet access)
        vpc = ec2.Vpc(
            self,
            "MainVpc",
            vpc_name=f"{env_name}-main-vpc",
            max_azs=2,
            nat_gateways=nat_gateways,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        # Optional: Add VPC flow logs to log bucket
        ec2.FlowLog(
            self,
            "VpcFlowLogs",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_s3(
                bucket=s3.Bucket.from_bucket_name(self, "LogBucketImport", log_bucket_name)
            ),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # --- 2. S3 Buckets ---
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

        # --- 3. IAM role (shared compute across EC2 / Batch / Lambda / API Gateway) ---
        shared_role = iam.Role(
            self,
            "SharedComputeRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ServicePrincipal("batch.amazonaws.com"),
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("apigateway.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayAdministrator"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
            ],
            role_name=f"{env_name}-shared-compute-role",
        )

        # --- 4. Tagging ---
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("Owner", "BaseStack")
        Tags.of(vpc).add("Purpose", "shared-network")
        Tags.of(main_bucket).add("Type", "primary")
        Tags.of(log_bucket).add("Type", "logs")

        # --- 5. Outputs ---
        CfnOutput(self, "VpcId", value=vpc.vpc_id)
        CfnOutput(self, "MainBucketName", value=main_bucket.bucket_name)
        CfnOutput(self, "LogBucketName", value=log_bucket.bucket_name)
        CfnOutput(self, "SharedRoleArn", value=shared_role.role_arn)