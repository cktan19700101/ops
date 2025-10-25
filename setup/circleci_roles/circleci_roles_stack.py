from aws_cdk import (
    Stack,
    aws_iam as iam,
    Duration,
)
from constructs import Construct


class CircleCIRolesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 org_id: str,
                 project_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        provider_arn = f"arn:aws:iam::{self.account}:oidc-provider/oidc.circleci.com/org/{org_id}"

        # Shared trust configuration for CircleCI
        trust = iam.FederatedPrincipal(
            provider_arn,
            conditions={
                "StringEquals": {
                    f"oidc.circleci.com/org/{org_id}:aud": org_id,
                },
                "StringLike": {
                    f"oidc.circleci.com/org/{org_id}:sub": f"org/{org_id}/project/{project_id}/user/*",
                },
            },
            assume_role_action="sts:AssumeRoleWithWebIdentity"
        )

        # === Infra Role ===
        infra_role = iam.Role(
            self, "CircleCIInfraRole",
            role_name="CircleCIInfraRole",
            assumed_by=trust,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEventBridgeFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
            ],
            max_session_duration=Duration.hours(1),
            description="CircleCI Infra role for provisioning CDK stacks and AWS resources"
        )

        # === App Role ===
        app_role = iam.Role(
            self, "CircleCIAppRole",
            role_name="CircleCIAppRole",
            assumed_by=trust,
            inline_policies={
                "AppDeploymentPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "lambda:UpdateFunctionCode",
                                "lambda:UpdateFunctionConfiguration",
                                "s3:PutObject",
                                "s3:GetObject",
                                "ecs:UpdateService",
                                "cloudfront:CreateInvalidation",
                                "ssm:GetParameter",
                                "ssm:GetParametersByPath",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=["*"],
                        )
                    ]
                )
            },
            max_session_duration=Duration.hours(1),
            description="CircleCI App deployment role with scoped permissions"
        )

        # Outputs
        self.infra_role_arn = infra_role.role_arn
        self.app_role_arn = app_role.role_arn