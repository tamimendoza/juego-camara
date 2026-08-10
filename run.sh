#!/bin/bash
# Launch the juego-camara pose silhouette application
# Usage: ./run.sh

set -e

cd "$(dirname "$0")"

# Download the MediaPipe pose landmarker model if not present
MODEL_DIR="models"
MODEL_FILE="${MODEL_DIR}/pose_landmarker_lite.task"
MODEL_URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float32/latest/pose_landmarker_lite.task"

if [ ! -f "${MODEL_FILE}" ]; then
    echo "Downloading pose landmarker model (lite)..."
    mkdir -p "${MODEL_DIR}"
    if command -v wget &> /dev/null; then
        wget -q -O "${MODEL_FILE}" "${MODEL_URL}"
    elif command -v curl &> /dev/null; then
        curl -sSL -o "${MODEL_FILE}" "${MODEL_URL}"
    else
        echo "Error: wget or curl is required to download the model file." >&2
        echo "Download manually from: ${MODEL_URL}" >&2
        exit 1
    fi
    echo "Model downloaded successfully."
fi

exec python3 -m src.main "$@"
