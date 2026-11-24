#!/usr/bin/env bash
set -o errexit

echo "Installing production dependencies..."
pip install -r requirements-render.txt

echo "Downloading ONNX model..."
python download_onnx.py

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Build completed successfully!"