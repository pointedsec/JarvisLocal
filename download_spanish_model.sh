#!/bin/bash
# download_spanish_model.sh
# Descarga el modelo de voz Piper TTS en español (es_ES-davefx-medium)
# para ser utilizado con el asistente de voz en OrangePi.

set -e

MODELS_DIR="models"
MODEL_NAME="es_ES-davefx-medium"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium"

echo "=== Descargando modelo de voz en español para Piper TTS ==="
echo "Modelo: ${MODEL_NAME}"
echo ""

# Crear directorio de modelos si no existe
mkdir -p "${MODELS_DIR}"

# Descargar el modelo .onnx
ONNX_FILE="${MODELS_DIR}/${MODEL_NAME}.onnx"
if [ -f "${ONNX_FILE}" ]; then
    echo "✓ El archivo ${ONNX_FILE} ya existe, omitiendo descarga."
else
    echo "Descargando ${MODEL_NAME}.onnx..."
    curl -L -o "${ONNX_FILE}" "${BASE_URL}/${MODEL_NAME}.onnx"
    echo "✓ Descargado: ${ONNX_FILE}"
fi

# Descargar el archivo de configuración .onnx.json
JSON_FILE="${MODELS_DIR}/${MODEL_NAME}.onnx.json"
if [ -f "${JSON_FILE}" ]; then
    echo "✓ El archivo ${JSON_FILE} ya existe, omitiendo descarga."
else
    echo "Descargando ${MODEL_NAME}.onnx.json..."
    curl -L -o "${JSON_FILE}" "${BASE_URL}/${MODEL_NAME}.onnx.json"
    echo "✓ Descargado: ${JSON_FILE}"
fi

echo ""
echo "=== Descarga completada ==="
echo "Los archivos del modelo están en: ${MODELS_DIR}/"
echo "  - ${ONNX_FILE}"
echo "  - ${JSON_FILE}"
echo ""
echo "Asegúrate de que 'piper_model_path' en config.ini apunte a:"
echo "  piper_model_path = ${ONNX_FILE}"
