# rdgen-ngx Local Builder
# Build RustDesk custom clients locally instead of using GitHub Actions
# Supports: Linux (x64/ARM64), Windows (cross-compile), Android
# Note: macOS requires actual Mac hardware

FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV RUST_VERSION=1.75.0
ENV FLUTTER_VERSION=3.24.5
ENV ANDROID_NDK_VERSION=r27c
ENV VCPKG_COMMIT=120deac3062162151622ca4860575a33844ba10b

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    cmake \
    curl \
    gcc \
    g++ \
    git \
    imagemagick \
    libayatana-appindicator3-dev \
    libasound2-dev \
    libclang-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgtk-3-dev \
    libpam0g-dev \
    libpulse-dev \
    libva-dev \
    libxcb-randr0-dev \
    libxcb-shape0-dev \
    libxcb-xfixes0-dev \
    libxdo-dev \
    libxfixes-dev \
    libssl-dev \
    libopus-dev \
    llvm-dev \
    nasm \
    ninja-build \
    pkg-config \
    python3 \
    python3-pip \
    rpm \
    unzip \
    wget \
    xz-utils \
    zip \
    # Windows cross-compilation
    mingw-w64 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip3 install requests pyzipper

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain ${RUST_VERSION}
ENV PATH="/root/.cargo/bin:${PATH}"

# Add cross-compilation targets
RUN rustup target add x86_64-pc-windows-gnu \
    && rustup target add x86_64-unknown-linux-gnu \
    && rustup target add aarch64-unknown-linux-gnu

# Install Flutter
RUN cd /opt && \
    wget -q https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz && \
    tar xf flutter_linux_${FLUTTER_VERSION}-stable.tar.xz && \
    rm flutter_linux_${FLUTTER_VERSION}-stable.tar.xz
ENV PATH="/opt/flutter/bin:${PATH}"

# Pre-configure Flutter
RUN flutter config --no-analytics && \
    flutter precache --linux

# Install vcpkg
RUN cd /opt && \
    git clone https://github.com/microsoft/vcpkg.git && \
    cd vcpkg && \
    git checkout ${VCPKG_COMMIT} && \
    ./bootstrap-vcpkg.sh
ENV VCPKG_ROOT="/opt/vcpkg"

# Create working directory
WORKDIR /build

# Copy build scripts
COPY build.sh /usr/local/bin/build.sh
COPY customize.py /usr/local/bin/customize.py
RUN chmod +x /usr/local/bin/build.sh

ENTRYPOINT ["/usr/local/bin/build.sh"]
