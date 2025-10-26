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
                 restrict_to_project: bool = True,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- 1️⃣ Ensure CircleCI OIDC provider exists ---
        circleci_oidc_provider = iam.OpenIdConnectProvider(
            self, "CircleCIOIDCProvider",
            url=f"https://oidc.circleci.com/org/{org_id}",
            client_ids=[org_id],  # CircleCI 'aud' claim = org_id
            thumbprints=["9e99a48a9960b14926bb7f3b02e22da0afd10df6"]
        )

        # Use the provider's ARN for trust policies
        provider_arn = circleci_oidc_provider.open_id_connect_provider_arn

        # --- 2️⃣ Build trust conditions ---
        conditions = {
            "StringEquals": {
                f"oidc.circleci.com/org/{org_id}:aud": org_id
            }
        }

        if restrict_to_project:
            conditions["StringLike"] = {
                f"oidc.circleci.com/org/{org_id}:sub":
                    f"org/{org_id}/project/{project_id}/user/*"
            }

        trust_principal = iam.FederatedPrincipal(
            federated=provider_arn,
            conditions=conditions,
            assume_role_action="sts:AssumeRoleWithWebIdentity"
        )

        # --- 3️⃣ Infra Role (full admin for provisioning) ---
        infra_role = iam.Role(
            self, "CircleCIInfraRole",
            role_name="CircleCIInfraRole",
            assumed_by=trust_principal,
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

        # --- 4️⃣ App Role (limited deployment permissions) ---
        app_role = iam.Role(
            self, "CircleCIAppRole",
            role_name="CircleCIAppRole",
            assumed_by=trust_principal,
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
                            resources=["*"]
                        )
                    ]
                )
            },
            # ✅ Attach AWS managed policies for full API Gateway & DynamoDB access
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayAdministrator"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
            ],
            max_session_duration=Duration.hours(1),
            description="CircleCI App deployment role with scoped permissions"
        )
        

        # --- 5️⃣ Outputs ---
        self.infra_role_arn = infra_role.role_arn
        self.app_role_arn = app_role.role_arn
        self.circleci_provider_arn = provider_arn