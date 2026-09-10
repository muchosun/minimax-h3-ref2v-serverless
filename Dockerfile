FROM runpod/worker-comfyui:5.8.6-base

# CUDA 13 is required by this candidate. Deploy only on compatible hosts.
RUN cd /comfyui && git fetch --depth 1 origin refs/tags/v0.30.1 && git checkout FETCH_HEAD && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install --no-cache-dir --force-reinstall torch==2.12.0 torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/cu130
COPY models.lock.json download_models.py verify_models.py /opt/h3/
# Download at BUILD time only; a failed SHA check fails the image build.
RUN /opt/venv/bin/python /opt/h3/download_models.py
COPY start.sh /opt/h3/start.sh
ENV COMFY_LOG_LEVEL=INFO HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["bash", "/opt/h3/start.sh"]
