"""
Streamlit Web UI for ML Inference

Interactive web interface for testing the inference model.
Supports both local FastAPI backend and AWS API Gateway endpoints.
"""

import streamlit as st
import requests
import numpy as np
from PIL import Image
import io
from typing import Optional
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="ML Inference Pipeline",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .title-emoji {font-size: 2.5rem;}
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .error-card {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR CONFIGURATION ====================
st.sidebar.title("Configuration")

# API Endpoint selection
api_mode = st.sidebar.radio(
    "Select API Mode",
    ["Local (FastAPI)", "AWS (API Gateway)"],
    help="Local: Uses uvicorn running locally. AWS: Uses deployed Lambda."
)

if api_mode == "Local (FastAPI)":
    local_host = st.sidebar.text_input(
        "FastAPI Host",
        value="http://localhost:8000",
        help="URL where FastAPI is running"
    )
    api_endpoint = f"{local_host}/predict"
    backend = "Local FastAPI"
else:
    api_endpoint = st.sidebar.text_input(
        "AWS API Gateway URL",
        value="",
        placeholder="https://xxxxx.execute-api.region.amazonaws.com/dev/predict",
        help="Full URL to AWS API Gateway endpoint"
    )
    backend = "AWS Lambda"

# Image preprocessing options
st.sidebar.title("Preprocessing")
confidence_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05,
    help="Predictions below this confidence will be flagged for active learning"
)

# ==================== MAIN TITLE ====================
st.title("ML Inference Pipeline")
st.caption(f"Backend: {backend} | Model: MobileNetV2 ONNX")

# ==================== INFORMATION TABS ====================
tab_inference, tab_info, tab_help = st.tabs(
    ["Inference", "Info", "Help"])

with tab_info:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Model", "MobileNetV2")
    with col2:
        st.metric("Runtime", "ONNX")
    with col3:
        st.metric("Backend", backend)

    st.markdown("---")
    st.subheader("System Architecture")
    st.code("""
    Client (This UI)
         ↓ HTTP POST /predict
    FastAPI / AWS Lambda
         ↓
    ONNX Runtime (MobileNetV2)
         ↓
    S3 (image storage) + DynamoDB (metadata) + CloudWatch (metrics)
    """, language="text")

with tab_help:
    st.markdown("""
    ### How to Use

    1. **Upload Image**: Select or drag-and-drop an image (JPG, PNG, AVIF)
    2. **Process**: Click "Run Inference" to classify the image
    3. **View Results**: See predictions, confidence, and latency
    4. **Active Learning**: Low-confidence predictions are flagged for review

    ### Supported Formats
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - AVIF (.avif)
    - Maximum size: 50 MB

    ### Response Structure
    ```json
    {
        "log_id": "unique-prediction-id",
        "class": 243,
        "confidence": 0.9876,
        "status": "logged",
        "latency_ms": 45.2
    }
    ```

    ### Active Learning
    Predictions with confidence < threshold are automatically queued for human review.
    This helps improve the model over time through continuous learning.
    """)

# ==================== MAIN INFERENCE INTERFACE ====================
with tab_inference:
    st.markdown("### Image Upload")

    # Image upload
    uploaded_file = st.file_uploader(
        "Choose an image to classify",
        type=["jpg", "jpeg", "png", "avif"],
        help="Drag and drop or click to select"
    )

    if uploaded_file is not None:
        # Display image
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Preview")
            image = Image.open(uploaded_file)
            st.image(image, width="stretch", caption="Uploaded Image")

            # Image info
            st.caption(f"""
            Size: {uploaded_file.size / 1024:.1f} KB
            Format: {uploaded_file.type}
            Dimensions: {image.size[0]}x{image.size[1]}
            """)

        with col2:
            st.markdown("#### Prediction")

            if api_endpoint and (api_mode == "Local (FastAPI)" or api_endpoint.startswith("https://")):
                if st.button("Run Inference", use_container_width=True):
                    with st.spinner("Processing image..."):
                        try:
                            # Prepare request
                            files = {
                                "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                            # Make request
                            response = requests.post(
                                api_endpoint, files=files, timeout=60)

                            if response.status_code == 200:
                                result = response.json()

                                # Display results
                                st.markdown(
                                    '<div class="success-card">', unsafe_allow_html=True)
                                st.markdown("**Inference Successful**")
                                st.markdown('</div>', unsafe_allow_html=True)

                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Predicted Class",
                                              result.get("class", "N/A"))
                                    st.metric("Status", result.get(
                                        "status", "N/A").replace("_", " ").title())

                                with col_b:
                                    confidence = result.get("confidence", 0)
                                    st.metric(
                                        "Confidence",
                                        f"{confidence:.2%}",
                                        delta=f"{'High' if confidence >= confidence_threshold else 'Low'}",
                                        delta_color="normal" if confidence >= confidence_threshold else 'inverse',
                                        delta_arrow="up" if confidence >= confidence_threshold else "down"

                                    )
                                    st.metric(
                                        "Latency", f"{result.get('latency_ms', 0):.1f}ms")

                                # Active Learning Flag
                                if confidence < confidence_threshold:
                                    st.warning(
                                        f"**Low Confidence Alert**\n\n"
                                        f"This prediction ({confidence:.2%}) is below the threshold ({confidence_threshold:.0%}) "
                                        f"and has been queued for human review (Active Learning)."
                                    )

                                # Details
                                with st.expander("Full Response"):
                                    st.json(result)

                                # Logging
                                st.success(
                                    f"✓ Logged with ID: `{result.get('log_id', 'N/A')}`")
                                st.caption(
                                    f"Timestamp: {datetime.now().isoformat()}")

                            else:
                                error_detail = response.text
                                st.markdown('<div class="error-card">',
                                            unsafe_allow_html=True)
                                st.markdown(
                                    f"**Error** (HTTP {response.status_code})")
                                st.markdown('</div>', unsafe_allow_html=True)
                                st.error(f"Response: {error_detail}")

                        except requests.exceptions.ConnectionError:
                            st.error(
                                f"Cannot connect to {api_endpoint}\n\n"
                                f"**Troubleshooting:**\n"
                                f"- Local mode: Ensure FastAPI is running (`uvicorn app.app_main:app --reload`)\n"
                                f"- AWS mode: Check that API Gateway URL is correct and accessible"
                            )
                        except requests.exceptions.Timeout:
                            st.error(
                                "Request timed out. The model might be slow to respond.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                if api_mode == "Local (FastAPI)":
                    st.warning(
                        "Please configure FastAPI host in the sidebar")
                else:
                    st.warning(
                        "Please paste AWS API Gateway URL in the sidebar")
    else:
        # No image uploaded
        st.info("Upload an image to get started")

        # Sample images info
        with st.expander("Sample Images for Testing"):
            st.markdown("""
            **Available test images:**
            - `tests/data/dog_001.avif` - Example dog image

            **Quick test command:**
            ```bash
            curl -X POST "http://localhost:8000/predict" \\
                 -H "Content-Type: multipart/form-data" \\
                 -F "file=@tests/data/dog_001.avif"
            ```
            """)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    AWS Serverless ML Pipeline | MobileNetV2 ONNX Runtime | Active Learning Enabled
    <br>
    For issues or feedback, visit the GitHub repository.
</div>
""", unsafe_allow_html=True)
