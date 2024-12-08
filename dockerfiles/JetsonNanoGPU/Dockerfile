# Base image JetPack 4.4
FROM nvcr.io/nvidia/l4t-base:r32.4.4

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/usr/local/cuda/bin:${PATH}" \
    LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    gnupg \
    ca-certificates \
    wget

RUN wget https://repo.download.nvidia.com/jetson/jetson-ota-public.asc -O jetson-ota-public.asc --no-check-certificate
RUN apt-key add jetson-ota-public.asc

# Add NVIDIA Jetson repositories
RUN echo "deb https://repo.download.nvidia.com/jetson/common r32.4 main" > /etc/apt/sources.list.d/nvidia-jetson.list && \
    echo "deb https://repo.download.nvidia.com/jetson/t210 r32.4 main" >> /etc/apt/sources.list.d/nvidia-jetson.list

RUN apt-get update && \
    apt-get install -y libcudnn8 \
    nvidia-container-toolkit \
    cuda-toolkit-10-2

# Install neccesary apt packages
RUN apt-get install python3-pip libopenblas-base libopenmpi-dev libomp-dev build-essential libhdf5-dev libhdf5-serial-dev libgfortran5 gfortran git -y

# Install python libs
RUN pip3 install setuptools wheel

RUN pip3 install 'Cython<3' && \
    wget https://nvidia.box.com/shared/static/p57jwntv436lfrd78inwl7iml6p13fzh.whl -O torch-1.8.0-cp36-cp36m-linux_aarch64.whl && \
    pip3 install numpy torch-1.8.0-cp36-cp36m-linux_aarch64.whl