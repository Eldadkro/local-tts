# Start from an Ubuntu 24.04 CUDA runtime image with cuDNN support for GPU inference.
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04

# Disable interactive Debian package prompts during image builds.
ENV DEBIAN_FRONTEND=noninteractive
# Prevent Python from writing .pyc bytecode files to disk.
ENV PYTHONDONTWRITEBYTECODE=1
# Make Python log output unbuffered so container logs appear immediately.
ENV PYTHONUNBUFFERED=1
# Tell the app to prefer GPU execution.
ENV TTS_DEVICE_MODE=gpu
# Expose all visible NVIDIA GPUs to the container.
ENV NVIDIA_VISIBLE_DEVICES=all
# Request compute and utility NVIDIA driver capabilities inside the container.
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Refresh apt package indexes, install runtime/build dependencies, then clean cached package lists.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        python3-pip \
        git \
        libsndfile1 \
        build-essential \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Register Python 3.12 as the default `python` executable.
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Define the virtual environment location.
ENV VIRTUAL_ENV=/opt/venv
# Create an isolated Python virtual environment for app dependencies.
RUN python -m venv "$VIRTUAL_ENV"
# Put the virtual environment binaries first on PATH.
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the working directory for all following Docker instructions.
WORKDIR /app

# Upgrade base Python packaging tools before installing project dependencies.
RUN python -m pip install --upgrade pip setuptools wheel

# Copy the project metadata files used during package installation.
COPY pyproject.toml README.md /app/
# Copy the application source code into the image.
COPY app /app/app
# Copy Docker-related runtime configuration files into the image.
COPY docker /app/docker

# Install CUDA 12.6 builds of PyTorch packages from the official PyTorch wheel index.
RUN python -m pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu126

# Install this project and its declared Python dependencies into the virtual environment.
RUN python -m pip install --no-cache-dir .

# Document the API and web UI ports exposed by the container.
EXPOSE 8000 8501

# Start Supervisor so it can manage the container's long-running processes.
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]
