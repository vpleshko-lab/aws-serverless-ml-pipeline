from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    RemovalPolicy
    # aws_sqs as sqs,
)
from constructs import Construct

class MlInfrastructureCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Ізольована мережа VPC
        self.vpc = ec2.Vpc(
            self, "MlOpsVpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, # NAT Gateway
                    cidr_mask=24
                )
            ]
        )
        self.mlflow_sg = ec2.SecurityGroup(
            self, "MlflowSecurityGroup",
            vpc=self.vpc,
            description="Allow access to Mlflow server",
            allow_all_outbound=True # Доступ до інтернету
        )
        self.mlflow_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5000),
            description="Allow Web UI access"
        )

        # security for DB RDS
        self.rds_sg = ec2.SecurityGroup(
            self, "RdsSecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS PostgreSQL",
            allow_all_outbound=True
        )
        # дозвіл на вхідний трафік від Mlflow
        self.rds_sg.add_ingress_rule(
            peer=self.mlflow_sg, # бейдж mlflow
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from MLflow server"
        )

        # 2. Створення базу даних RDS PostgreSQL
        self.postgres_db = rds.DatabaseInstance(
            self, "MlflowPostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO # t3.micro
            ),
            vpc=self.vpc,
            security_groups=[self.rds_sg], # security group
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            database_name="mlflow_db" # всередині системи
        ),

        # створення s3 bucket'y
        self.model_bucket = s3.Bucket(
            self, "MlflowModelBucket",
            bucket_name="serverless-models-artifacts",
            encryption=s3.BucketEncryption.S3_MANAGED, # шифрування даних
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL # повністю закритий доступ з інтернету
        )

        # -- МІГРАЦІЯ створених компонентів черех UI --
        # імпорт існючого бакету за його назвою (той, що я створював в UI)
        self.existing_photo_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingPhotoBucket",
            bucket_name = "aws-ml-logs"
        )
        self.inference_logs_table = dynamodb.Table(
            self, "InferenceLogsTable",
            table_name="InferenceLogs", # навза у консолі
            partition_key=dynamodb.Attribute(
                name="prediction_id", # partititon key
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", # sort key
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.RETAIN
        )
