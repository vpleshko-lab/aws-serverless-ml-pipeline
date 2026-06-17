import os
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."))


class MlInfrastructureCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. МЕРЕЖЕВА ІНФРАСТРУКТУРА ТА БАЗА ДАНИХ (Нові ресурси)

        # VPC для безпечного середовища MLflow та RDS
        self.vpc = ec2.Vpc(
            self, "MlOpsVpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(
                    name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24)
            ]
        )

        # База даних RDS PostgreSQL для метаданих MLflow
        self.rds_db = rds.DatabaseInstance(
            self, "MlflowPostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            allocated_storage=20,
            max_allocated_storage=100,
            database_name="mlflow_db",
            removal_policy=RemovalPolicy.RETAIN
        )

        # Новий бакет для артефактів моделей MLflow
        self.model_bucket = s3.Bucket(
            self, "MlflowArtifactsBucket",
            bucket_name="serverless-models-artifacts",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False
        )

        # 2. МІГРАЦІЯ ІСНУЮЧИХ РЕСУРСІВ

        # Підключаємо існуючі S3 бакети
        self.ml_logs_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingMlLogsBucket",
            bucket_name="aws-ml-logs"
        )

        self.labeling_queue_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingLabelingQuequeBucket",
            bucket_name="aws-labeling-queque"
        )

        # Описуємо ВЖЕ ІМПОРТОВАНУ таблицю DynamoDB
        self.inference_logs_table = dynamodb.Table(
            self, "InferenceLogsTable",
            table_name="InferenceLogs",
            partition_key=dynamodb.Attribute(
                name="prediction_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.RETAIN
        )

        # Lambda-функція інференсу (Docker-контейнер з кореня проєкту)
        self.inference_lambda = _lambda.DockerImageFunction(
            self, "MlEdgeInferenceLambda",
            function_name="ml-serverless-inference",
            code=_lambda.DockerImageCode.from_image_asset(project_root),
            timeout=Duration.minutes(5),
            memory_size=1024
        )

        # Lambda-функція Active Learning відбору (Docker-контейнер з кореня проєкту)
        self.data_selector_lambda = _lambda.DockerImageFunction(
            self, "MlDataSelectorLambda",
            function_name="ml-serverless-data-selector",
            code=_lambda.DockerImageCode.from_image_asset(project_root),
            timeout=Duration.minutes(10),
            memory_size=2048,
            environment={
                "LOGS_BUCKET": self.ml_logs_bucket.bucket_name,
                "QUEUE_BUCKET": self.labeling_queue_bucket.bucket_name,
                "DYNAMODB_TABLE": self.inference_logs_table.table_name
            }
        )

        # 3. АВТОМАТИЗАЦІЯ ТА КЕРУВАННЯ ДОСТУПАМИ (IAM & Крон-тригери)

        # правило EventBridge для запуску відбору щонеділі о 12:00 UTC
        self.cron_rule = events.Rule(
            self, "WeeklyDataSelectorTrigger",
            rule_name="weekly-active-learning-selector",
            schedule=events.Schedule.cron(
                minute="0", hour="12", week_day="SUN"),
            enabled=False
        )

        self.cron_rule.add_target(
            targets.LambdaFunction(self.data_selector_lambda))

        # права доступу
        self.ml_logs_bucket.grant_read_write(self.inference_lambda)
        self.inference_logs_table.grant_read_write_data(self.inference_lambda)

        self.ml_logs_bucket.grant_read(self.data_selector_lambda)
        self.inference_logs_table.grant_read_write_data(
            self.data_selector_lambda)
        self.labeling_queue_bucket.grant_read_write(self.data_selector_lambda)
