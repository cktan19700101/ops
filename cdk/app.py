#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.base_stack import BaseStack

app = cdk.App()

# Allow region/account to be auto-detected from environment
BaseStack(
    app,
    "OpsBaseStack",
    env=cdk.Environment(
        account=cdk.Aws.ACCOUNT_ID,
        region=cdk.Aws.REGION
    ),
)

app.synth()
