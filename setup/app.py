#!/usr/bin/env python3
import os
import aws_cdk as cdk
from circleci_roles.circleci_roles_stack import CircleCIRolesStack

app = cdk.App()

# Use either context (-c) or environment variables
org_id = app.node.try_get_context("circleci_org_id") or os.getenv("CIRCLECI_ORG_ID")
project_id = app.node.try_get_context("circleci_project_id") or os.getenv("CIRCLECI_PROJECT_ID")

if not org_id or not project_id:
    raise ValueError("Both 'circleci_org_id' and 'circleci_project_id' are required. "
                     "Pass via -c or environment variables.")

CircleCIRolesStack(
    app, "CircleCIRolesStack",
    org_id=org_id,
    project_id=project_id,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "ap-southeast-1"),
    ),
)

app.synth()

# cdk deploy \
#   -c circleci_org_id=\
#   -c circleci_project_id=
