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
    echo "deb https://repo.download.nvidia.com/jetson/t210 r32.4 main" >> /etc/apt/sources.list.d/nvidia-jetson.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libcudnn8 \
    nvidia-container-toolkit \
    cuda-toolkit-10-2

# Install neccesary apt packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    libopenblas-base \
    libopenmpi-dev \
    libomp-dev \
    build-essential \
    libhdf5-dev \
    libhdf5-serial-dev \
    libblas-dev \
    liblapack-dev \
    libgfortran5 \
    gfortran \
    git

# Install Python libraries
RUN pip3 install setuptools wheel

RUN pip3 install --no-cache-dir 'Cython<3'

RUN wget https://raw.githubusercontent.com/yihuajack/h5py-aarch64/refs/heads/main/h5py-3.1.0-cp36-cp36m-linux_aarch64.whl && \
    pip3 install --no-cache-dir h5py-3.1.0-cp36-cp36m-linux_aarch64.whl

RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install statsmodels Levenshtein tqdm

RUN wget developer.download.nvidia.com/compute/redist/jp/v44/tensorflow/tensorflow-1.15.4+nv20.12-cp36-cp36m-linux_aarch64.whl && \
    python3 -m pip install --no-cache-dir tensorflow-1.15.4+nv20.12-cp36-cp36m-linux_aarch64.whl

RUN rm -rf h5py-3.1.0-cp36-cp36m-linux_aarch64.whl && \
    rm -rf tensorflow-1.15.4+nv20.12-cp36-cp36m-linux_aarch64.whl

RUN pip3 install chiron

# Optional install psutil to monitor metris
RUN pip3 install psutil 

# Optional install flask to run bascalling from urls
RUN pip3 install flask

#Opitonal install azure cosmos to saving result and metrics
RUN pip3 install azure-cosmos && \
   pip3 install azure-identity && \
   pip3 install python-dotenv

# Download example data and basecaller
RUN git clone --recursive https://github.com/Drigix/jetson-basecalling.git 

# Add a simple command to keep the container alive
CMD ["tail", "-f", "/dev/null"]

# Run flask listener
#CMD ["python3", "/jetson-basecalling/Chiron/flask_listener.py"]