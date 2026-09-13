# Dockerfile = a recipe for building your app into a container image.
# Each instruction below adds one "layer" to that image.

# Start from an official, lightweight Python image (not the full OS,
# just enough to run Python) — this replaces needing Python installed
# on the host machine at all.
FROM python:3.12-slim

# Set the working directory INSIDE the container. Every command below
# runs relative to this folder.
WORKDIR /app

# Copy just the requirements file first (not the whole project yet).
# This is a deliberate ordering trick: Docker caches each layer, and
# your dependencies change far less often than your code. By copying
# requirements.txt first and installing them in their own layer,
# Docker can reuse that cached layer on future builds and skip
# reinstalling everything, as long as requirements.txt hasn't changed.
COPY requirements.txt .

# IMPORTANT: install the CPU-only build of PyTorch FIRST, from
# PyTorch's own CPU-specific package index. Without this,
# sentence-transformers (installed in the next step) would pull in
# the full GPU/CUDA version of PyTorch by default — several
# gigabytes of NVIDIA libraries that this container doesn't need or
# use, since it has no GPU. Installing the CPU version first means
# the next step sees PyTorch is already satisfied and skips the huge
# GPU download entirely.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# NOW copy the rest of your actual project code.
COPY . .

# Document which port the app listens on (this line is informational;
# the real port mapping happens when you RUN the container).
EXPOSE 8000

# The command that runs when the container starts.
# --host 0.0.0.0 is required (not 127.0.0.1) so the server accepts
# connections from OUTSIDE the container, not just from within it.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
