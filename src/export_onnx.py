import torch
import torchvision.models as models


def export_model():
    # Load pretrained model
    model = models.mobilenet_v2(weights="MobileNet_V2_Weights.DEFAULT")
    model.eval()

    # Make fake input image
    dummy_input = torch.randn(1, 3, 224, 224)

    torch.onnx.export(
        model,
        dummy_input,
        "model.onnx",
        export_params=True,
        opset_version=12,
        input_names=['input'],
        output_names=['output']
    )
    print("Model is succsesfully saved -> .onnx")


if __name__ == "__main__":
    export_model()
