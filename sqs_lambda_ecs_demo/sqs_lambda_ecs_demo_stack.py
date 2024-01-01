from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_ecs,
    aws_ec2,
    aws_iam, 
    aws_ecr_assets, 
    aws_lambda, 
    aws_lambda_event_sources,
    aws_sqs, Duration, Size
)
from constructs import Construct

class SqsLambdaEcsDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.vpc_id = "vpc_id_placeholder"
        self.container_name = "ecsTaskContainerImage"
        self.build_sqs()
        self.build_lambda_function()
        
        self.create_image_asset()
        self.create_ecs_cluster()
        self.create_ecs_task_definition()
        
        self.configure_lambda_env()


    def build_sqs(self):
        self.dead_letter_queue = aws_sqs.Queue(
            scope=self, 
            id="sqsLambdaEcsDemoDeadLetterQueue.fifo", 
            queue_name="sqsLambdaEcsDemoDeadLetterQueue.fifo", 
            visibility_timeout=Duration.seconds(30), 
            fifo=True
        )
        self.dead_letter_queue.apply_removal_policy(RemovalPolicy.DESTROY)
        
        self.queue = aws_sqs.Queue(
            scope=self, 
            id="sqsLambdaEcsDemoQueue.fifo", 
            queue_name="sqsLambdaEcsDemoQueue.fifo", 
            visibility_timeout=Duration.minutes(3), 
            fifo=True, 
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=2,
                queue=self.dead_letter_queue
            )
        )
        self.queue.apply_removal_policy(RemovalPolicy.DESTROY)
        
        
    def build_lambda_function(self):
        self.lambda_function = aws_lambda.Function(
            scope=self, 
            id="sqsLambdaEcsDemoLambda", 
            function_name="sqsLambdaEcsDemoLambda", 
            code=aws_lambda.Code.from_asset(
                path="lib/lambda"
            ), 
            handler="handler.handler", 
            runtime=aws_lambda.Runtime.PYTHON_3_11, 
            timeout=Duration.minutes(2)
        )
        
        self.lambda_function.apply_removal_policy(RemovalPolicy.DESTROY)
        self.lambda_function.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW, 
            actions=[
                'ec2:DescribeSubnets', 
                # 'ecs:RunTask'
            ], 
            resources=["*"]
        ))
        self.lambda_function.add_event_source(
            source=aws_lambda_event_sources.SqsEventSource(
                queue=self.queue,
                batch_size=1
            )
        )
        
        
    
    def create_image_asset(self):
        self.image_asset = aws_ecr_assets.DockerImageAsset(
            scope=self,
            id="sqsLambdaEcsDemoImage",
            asset_name="sqsLambdaEcsDemoImage",
            directory="lib/ecs"
        )
        

    def create_ecs_cluster(self):

        self.vpc = aws_ec2.Vpc.from_lookup(
            scope=self, 
            id="sqsLambdaEcsDemoVPC", 
            vpc_id=self.vpc_id,
            region='ap-northeast-1'
        )
        
        self.cluster = aws_ecs.Cluster(
            scope=self,
            id="sqsLambdaEcsDemoCluster", 
            cluster_name="sqsLambdaEcsDemoCluster",
            vpc=self.vpc, 
            container_insights=False
        )
        self.cluster.apply_removal_policy(RemovalPolicy.DESTROY)
            
    
    def create_ecs_task_definition(self):
        # create task definition 
        self.task_definition = aws_ecs.FargateTaskDefinition(
            scope=self, 
            id="sqsLambdaEcsDemoTaskDeinition",
            family="sqsLambdaEcsDemoTaskDeinition",            
            memory_limit_mib =1024,
            cpu=512,
            runtime_platform=aws_ecs.RuntimePlatform(
                operating_system_family=aws_ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=aws_ecs.CpuArchitecture.ARM64,
            )
        )
        self.task_definition.apply_removal_policy(RemovalPolicy.DESTROY)
        
        self.task_definition.add_to_execution_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW, 
            actions=[
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ], 
            resources=["*"]
        ))
    
        
        self.task_definition.add_to_task_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW, 
            actions=[
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ], 
            resources=["*"]
        ))

        self.task_definition.add_container(
            id="ecsTaskContainerImage",
            image=aws_ecs.ContainerImage.from_docker_image_asset(self.image_asset),
            container_name=self.container_name,
            logging=aws_ecs.LogDrivers.aws_logs(
                stream_prefix="sqsLambdaEcsDemo",
                mode=aws_ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            )
        )
        
        self.task_definition.grant_run(self.lambda_function)
     

    def configure_lambda_env(self):
        self.lambda_function.add_environment(key="VPC_ID", value=self.vpc_id)
        self.lambda_function.add_environment(key="CLUSTER_NAME", value=self.cluster.cluster_name)
        self.lambda_function.add_environment(key="CONTAINER_NAME", value=self.container_name)
        self.lambda_function.add_environment(key="TASK_DEFINITION_ARN", value=self.task_definition.task_definition_arn)
