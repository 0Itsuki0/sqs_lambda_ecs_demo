import aws_cdk as core
import aws_cdk.assertions as assertions

from sqs_lambda_ecs_demo.sqs_lambda_ecs_demo_stack import SqsLambdaEcsDemoStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sqs_lambda_ecs_demo/sqs_lambda_ecs_demo_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SqsLambdaEcsDemoStack(app, "sqs-lambda-ecs-demo")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
