# Base image JetPack 6.1
FROM nvcr.io/nvidia/l4t-base:r36.2.0

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/usr/local/cuda/bin:${PATH}" \
    LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Install necesary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    nano \
    python3-pip \
    python3-dev \
    libopenblas-dev && \
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/arm64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    apt-get update && apt-get install -y --no-install-recommends \
    libcublas-12-6 \
    cuda-toolkit-12-6 \
    libcudnn8 \
    libcudnn8-dev

# Install neccesary apt packages
RUN python3 -m pip install --upgrade pip && \
    pip3 install --no-cache-dir \
        filelock==3.13.1 \
        fsspec==2024.2.0 \
        Jinja2==3.1.3 \
        MarkupSafe==2.1.5 \
        mpmath==1.3.0 \
        networkx==3.2.1 \
        numpy==1.26.3 \
        pillow==10.2.0 \
        pip==22.0.2 \
        setuptools==59.6.0 \
        sympy==1.13.1 \
        typing_extensions==4.9.0

# Install torch
ENV TORCH_INSTALL=https://developer.download.nvidia.cn/compute/redist/jp/v60/pytorch/torch-2.4.0a0+07cecf4168.nv24.05.14710581-cp310-cp310-linux_aarch64.whl
RUN python3 -m pip install --no-cache-dir $TORCH_INSTALL
