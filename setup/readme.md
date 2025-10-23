# CircleCI Connectivity for CDK deployment

## Requirements
1. aws accountId
2. circleci org id
3. circleci projectid

# # aws cloudformation deploy     --template-file /home/ubuntu/playground/ops/setup/circleci-aws-infra-role.yml     --stack-name circleci-roles     --parameter-overrides     AccountId=    CircleCIOrgId=  CircleCIProjectId=     --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# # troubleshooting
# # aws cloudformation describe-stack-events --stack-name circleci-roles   --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[Timestamp,LogicalResourceId,ResourceStatusReason]"   --output table