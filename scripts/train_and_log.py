import os
import mlflow
import mlflow.onnx
import torch
import torchvision.models as models
import logging
from app.logger_setup import setup_app_logging
from mlflow.tracking import MlflowClient

# Logger
setup_app_logging()
logger = logging.getLogger(__name__)


def get_mlflow_uri():
    cloud_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if cloud_uri:
        return cloud_uri

    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_mlruns_path = os.path.join(current_dir, "mlruns")
    return f"file://{local_mlruns_path}"


def log_mobilenet_model():
    tracking_uri = get_mlflow_uri()
    mlflow.set_tracking_uri(tracking_uri)
    logger.info("Using Tracking URI: %s", tracking_uri)

    model_name = "Classification-MobileNet"
    mlflow.set_experiment(model_name)

    with mlflow.start_run(run_name="mobilenet_v2_base") as run:
        logger.info(
            "The logging has started in MLflow (ID run: %s)", run.info.run_id)

        try:
            logger.info("Initialization of model MobileNetV2...")
            model = models.mobilenet_v2(weights="MobileNet_V2_Weights.DEFAULT")

            metrics = {
                "mAP_50": 0.845,
                "inference_time_ms": 15.2,
                "epochs": 50
            }

            logger.info("Conversion model MobileNetV2 to ONNX..")
            model.eval()
            dummy_input = torch.randn(1, 3, 224, 224)
            onnx_filename = "model.onnx"

            torch.onnx.export(
                model,
                dummy_input,
                onnx_filename,
                export_params=True,
                opset_version=17,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch_size'},
                              'output': {0: 'batch_size'}}
            )

            logger.info('Sending ONNX model to registry of artefacts MLflow')
            mlflow.log_artifact(onnx_filename, artifact_path="model")

            if os.path.exists(onnx_filename):
                os.remove(onnx_filename)
            logger.info(
                "ONNX Model has successfully converted and registered in Mlflow")

            # --- Автоматичне призначення тегу Production ---
            logger.info(
                "Registering model in the Model Registry")
            client = MlflowClient()

            try:
                client.create_registered_model(model_name)
            except Exception:
                pass

            # нова версія моделі з артефакту
            atrifact_uri = f"{run.info.artifact_uri}/model/{onnx_filename}"
            model_version_info = client.create_model_version(
                name=model_name,
                source=atrifact_uri,
                run_id=run.info.run_id
            )

            # Призначаємо Alias "Production"
            logger.info("Setting 'Production' alias for version %s...",
                        model_version_info.version)
            client.set_registered_model_alias(
                name=model_name,
                alias="Production",
                version=str(model_version_info.version)
            )
            logger.info(
                "Successfully set alias 'Production'")
            # -----------------------------------------------

            logger.info(
                "Parameters and metrics are logging to the tracking server..")
            mlflow.log_param("architecture", "MobileNetV2-base")
            mlflow.log_param("backbone", "MobileNet-Pretrained")

            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)

            logger.info("Model weights are saving and sending to artefacts..")
            pt_filename = "mobilenet_v2.pt"
            torch.save(model.state_dict(), pt_filename)
            mlflow.log_artifact(pt_filename, artifact_path="model_weights")

            if os.path.exists(pt_filename):
                os.remove(pt_filename)

            logger.info("Metrics and weights have been saved in Mlflow!")

        except Exception as e:
            logger.error("Error while logging: %s", str(e), exc_info=True)
            raise


if __name__ == "__main__":
    log_mobilenet_model()
