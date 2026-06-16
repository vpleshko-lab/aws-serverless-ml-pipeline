import aws_cdk as core
import aws_cdk.assertions as assertions

from ml_infrastructure_cdk.ml_infrastructure_cdk_stack import MlInfrastructureCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ml_infrastructure_cdk/ml_infrastructure_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MlInfrastructureCdkStack(app, "ml-infrastructure-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
