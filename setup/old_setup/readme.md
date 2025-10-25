# CircleCI Connectivity for CDK deployment

## Requirements
1. aws accountId
2. circleci org id
3. circleci projectid

# # troubleshooting by printing failed status output
aws cloudformation describe-stack-events --stack-name circleci-aws-infra-role   --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[Timestamp,LogicalResourceId,ResourceStatusReason]"   --output table


# # delete it
aws cloudformation delete-stack --stack-name circleci-aws-infra-role
