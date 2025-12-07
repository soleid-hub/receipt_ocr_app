#Python 3.12
FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

#osライブラリのインストール
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*