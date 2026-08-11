#!/bin/bash
# Launch the Mario Face Jump game (real face overlay instead of Mario head)
# Usage: ./run_mario_face.sh

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

# Download the MediaPipe face landmarker model if not present
FACE_MODEL_FILE="${MODEL_DIR}/face_landmarker.task"
FACE_MODEL_URL="https://storage.googleapis.com/mediapipe-models/face_landmarker/facelandmarker/float32/latest/face_landmarker.task"

if [ ! -f "${FACE_MODEL_FILE}" ]; then
    echo "Downloading face landmarker model..."
    mkdir -p "${MODEL_DIR}"
    if command -v wget &> /dev/null; then
        wget -q -O "${FACE_MODEL_FILE}" "${FACE_MODEL_URL}"
    elif command -v curl &> /dev/null; then
        curl -sSL -o "${FACE_MODEL_FILE}" "${FACE_MODEL_URL}"
    else
        echo "Error: wget or curl is required to download the face model file." >&2
        echo "Download manually from: ${FACE_MODEL_URL}" >&2
        exit 1
    fi
    echo "Face model downloaded successfully."
fi

exec python3 -m src.mario_face_main "$@"
