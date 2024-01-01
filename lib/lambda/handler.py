
import boto3
import os

ec2 = boto3.client('ec2')
ecs = boto3.client('ecs')

VPC_ID = os.getenv('VPC_ID')
CLUSTER_NAME = os.getenv('CLUSTER_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
# TASK_DEFINITION_NAME = os.getenv('TASK_DEFINITION_NAME')
TASK_DEFINITION_ARN = os.getenv('TASK_DEFINITION_ARN')

def get_subnets(vpc_id: str = VPC_ID) -> list:
    response = ec2.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    subnets = response['Subnets']
    subnet_ids = [i["SubnetId"] for i in subnets]
    print("subnet ids: ", subnet_ids)
    return subnet_ids


subnet_ids = get_subnets()

def run_ecs_task(message: str):
    response = ecs.run_task(
        cluster=CLUSTER_NAME,
        taskDefinition=TASK_DEFINITION_ARN,
        launchType='FARGATE',
        networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': subnet_ids, 
            'assignPublicIp': 'ENABLED'
        }},
        overrides={
            'containerOverrides': [
                {
                    'name': CONTAINER_NAME,
                    'command': ["python3","process.py", message]
                }
            ]
        }
    )
    print(response) 
    return



def handler(event, context):
    print(event)
    records = event["Records"]
    for record in records:
        message = record["body"]
        print(message)
        run_ecs_task(message=message)   
    return {
        'statusCode': 200,
        'body': "success"
    }