FROM runpod/worker-comfyui:5.8.6-base

# CUDA 13 is required by this candidate. Deploy only on compatible hosts.
RUN apt-get update && apt-get install -y --no-install-recommends aria2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Same ComfyUI release and torch major/minor as the successful A40 Pod test.
# The final Serverless image still requires its own GPU acceptance test.
RUN cd /comfyui && git fetch --depth 1 origin 12d5279438bfefc058a269eae805ceab6047777f && git checkout FETCH_HEAD && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install --no-cache-dir --force-reinstall torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 \
      --index-url https://download.pytorch.org/whl/cu130 && \
    /opt/venv/bin/pip install --no-cache-dir 'transformers>=4.50.3,<5' 'huggingface-hub<1.0' && \
    /opt/venv/bin/pip check && \
    timeout 300 /opt/venv/bin/python main.py --quick-test-for-ci --cpu
COPY models.lock.json download_models.py verify_models.py /opt/h3/
# Download at BUILD time only; a failed SHA check fails the image build.
RUN /opt/venv/bin/python /opt/h3/download_models.py
RUN /opt/venv/bin/python /opt/h3/verify_models.py && \
    /opt/venv/bin/pip freeze > /opt/h3/pip-freeze.txt
COPY start.sh /opt/h3/start.sh
ENV COMFY_LOG_LEVEL=INFO HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["bash", "/opt/h3/start.sh"]
