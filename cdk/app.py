#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.base_stack import BaseStack

app = cdk.App()

# Allow region/account to be auto-detected from environment
env_name = app.node.try_get_context("env") or "dev"

BaseStack(
    app,
    f"OpsStack-{env_name}",
    env=cdk.Environment(
    ),
)

app.synth()