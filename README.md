# 🤖 Asistente de Voz Local con Ollama (STT, LLM, TTS) — OrangePi Edition

Un asistente de voz manos libres en Python que funciona 100% localmente, optimizado para **OrangePi con 8GB de RAM** y configurado para **escuchar y responder siempre en español**. Utiliza openwakeword para detección de palabra clave, webrtcvad para detección de silencio, Whisper de OpenAI para transcripción, y Ollama para respuestas generativas con IA.

```mermaid
flowchart LR
    A[Micrófono] --> B(openwakeword);
    B -- "hey jarvis" --> C(webrtcvad);
    C -- "Graba hasta silencio" --> D[faster-whisper STT];
    D -- "Transcribe audio en español" --> E[Ollama LLM];
    E -- "Genera respuesta en español" --> F[Piper TTS];
    F -- "Habla la respuesta" --> G[Altavoz];
```

## 💡 Características
- **100% Local**: No se requieren servicios en la nube para STT, TTS ni el LLM.
- **Manos Libres**: Usa openwakeword para detección de palabra clave.
- **TTS de Baja Latencia**: Usa el motor Piper TTS con voz en español para una salida de voz rápida y de alta calidad.
- **STT Optimizado**: Usa modelos faster-whisper multilingüe para transcripción precisa en español.
- **Grabación Inteligente**: Usa webrtcvad (Detección de Actividad de Voz) para dejar de grabar automáticamente cuando dejas de hablar.
- **LLM Flexible**: Fácilmente configurable para usar cualquier modelo soportado por tu instancia local de Ollama (ej. llama3, mistral, phi3).
- **Audio Multiplataforma**: Usa sounddevice para entrada/salida de audio.
- **Configurable**: Los ajustes se pueden modificar vía `config.ini` y argumentos de línea de comandos.
- **Optimizado para OrangePi**: Configurado para CPU ARM con 8GB de RAM, usando modelos ligeros y configuración `int8`.

## 🔩 1. Requisitos Previos

### 🍊 A. Hardware
- **OrangePi** (u otra SBC ARM64) con al menos **8GB de RAM**
- Micrófono USB o integrado
- Altavoz o salida de audio

### 🦙 B. Ollama
Debes tener la aplicación Ollama instalada y ejecutándose en tu OrangePi.

```bash
# Instalar Ollama en ARM64
curl -fsSL https://ollama.ai/install.sh | sh
```

### 📦 C. Descargar un Modelo de Ollama
Necesitas al menos un modelo descargado para que Ollama funcione.
```bash
# El modelo por defecto es llama3 (funciona bien con 8GB de RAM)
ollama pull llama3

# Alternativa más ligera si necesitas más rendimiento:
# ollama pull phi3:mini
```

### ⚙️ D. Dependencias del Sistema
Las librerías de audio requieren paquetes del sistema instalados.

**En OrangePi (Debian/Ubuntu/Armbian):**
```bash
sudo apt-get update && sudo apt-get install -y portaudio19-dev ffmpeg python3-dev python3-venv build-essential curl
```

### 🗣️ E. Modelos de Wake-Word y TTS
Este proyecto incluye modelos de wake-word empaquetados en el directorio `models/`. **El modelo de voz TTS en español debe descargarse por separado:**

```bash
# Descargar el modelo de voz en español para Piper TTS
chmod +x download_spanish_model.sh
./download_spanish_model.sh
```

Este script descarga el modelo `es_ES-davefx-medium` de Piper TTS desde Hugging Face.

## 🔧 2. Instalación
Clona este repositorio en tu OrangePi y navega al directorio del proyecto.
```bash
git clone https://github.com/pointedsec/JarvisLocal.git
cd JarvisLocal
```

Crea y activa un entorno virtual de Python (recomendado).
```bash
# Crear el entorno
python3 -m venv venv

# Activarlo
source venv/bin/activate
```

Instala el proyecto:
```bash
pip install .
```

Para desarrollo (incluye dependencias de testing):
```bash
pip install -e .[test]
```

En la primera ejecución, la aplicación descargará automáticamente el modelo `faster-whisper` necesario.

## ⌨️ 3. Ejecutar el Asistente
Puedes ejecutar el asistente localmente con Python o vía Docker. **Todos los comandos deben ejecutarse desde la raíz del directorio del proyecto.**

### 🐍 A. Ejecutar Localmente con Python
Asegúrate de que tu aplicación Ollama esté ejecutándose. Luego, inicia el asistente:
```bash
python run.py
```
O, si has instalado el paquete, puedes usar el punto de entrada:
```bash
ollama-voice-assistant
```

Cuando esté listo, verás el mensaje: `Ready! Listening for 'hey jarvis'...`

**Cómo Interactuar:**
1.  **Di la palabra clave** (ej. "Hey jarvis").
2.  El asistente responderá "¿Sí?" y comenzará a escuchar.
3.  **Habla tu comando en español** (ej. "¿Quién ganó la guerra de 1812?").
4.  El asistente transcribirá tu audio, lo enviará a Ollama, y hablará la respuesta en español. Luego volverá a escuchar la palabra clave.

**Comandos Especiales:**
- `"salir"`, `"adiós"`, `"goodbye"` o `"exit"`: Detiene el asistente.
- `"nuevo chat"`, `"reiniciar chat"`, `"borrar historial"`: Limpia el historial de conversación del LLM.

### 🐋 B. Ejecutar con Docker
**1. Construir la Imagen (en OrangePi ARM64):**
```bash
docker build -t jarvis-local .
```

**2. Preparar Configuración:**
Puedes listar los dispositivos de audio disponibles:
```bash
python run.py --list-devices
```
Edita `config.ini` con el `device_index` correcto.

**3. Ejecutar el Contenedor (Linux/OrangePi):**
```bash
docker run --rm -it \
  --network=host \
  --device /dev/snd \
  -v ./config.ini:/app/config.ini:ro \
  jarvis-local
```
- `--network=host`: Necesario para que el contenedor acceda a Ollama en `http://localhost:11434`.
- `--device /dev/snd`: Da acceso al contenedor a los dispositivos de sonido del host.
- `-v ./config.ini...`: Monta tu archivo de configuración local como solo lectura.

## 🎛️ 4. Configuración
Personaliza el asistente editando `config.ini` o proporcionando argumentos de línea de comandos. Los argumentos siempre sobrescriben la configuración del archivo.

**Comandos de Ejemplo:**
```bash
# Ejecutar con diferente umbral de wakeword y agresividad VAD
python run.py --wakeword-threshold 0.5 --vad-aggressiveness 1

# Ejecutar usando un modelo Ollama diferente
python run.py --ollama-model mistral

# Cambiar el idioma de Whisper (por defecto: es)
python run.py --whisper-language es
```

**Argumentos Comunes:**
- `--list-devices`: Lista dispositivos de entrada de audio y sale.
- `--list-output-devices`: Lista dispositivos de salida de audio y sale.
- `--debug`: Habilita logging detallado de debug.
- `--ollama-model`: Nombre del modelo Ollama a usar (ej. `llama3`, `mistral`).
- `--whisper-model`: Nombre del modelo `faster-whisper` (ej. `tiny`, `base`, `small`).
- `--whisper-language`: Código de idioma para Whisper (ej. `es`, `en`). Por defecto: `es`.
- `--wakeword`: La frase de activación a escuchar.
- `--device-index`: El índice entero de tu micrófono.
- `--piper-output-device-index`: El índice entero de tu altavoz.
- `--system-prompt`: Un prompt de sistema personalizado o ruta a un archivo `.txt`.

Para la lista completa de opciones configurables, ve las secciones `[Models]` y `[Functionality]` en `config.ini`.

### 🍊 Optimizaciones para OrangePi

La configuración por defecto ya está optimizada para OrangePi con 8GB de RAM:

| Ajuste | Valor | Razón |
|--------|-------|-------|
| `whisper_model` | `base` | Balance entre precisión y velocidad en CPU ARM |
| `whisper_device` | `cpu` | OrangePi no tiene GPU CUDA |
| `whisper_compute_type` | `int8` | Cuantización para menor uso de memoria y mayor velocidad |
| `whisper_language` | `es` | Transcripción en español |
| `max_history_tokens` | `1024` | Reduce uso de memoria del historial de chat |
| `gc_interval` | `5` | Recolección de basura más frecuente para liberar memoria |
| `ollama_model` | `llama3` | Funciona bien con cuantización en 8GB de RAM |

Si experimentas lentitud, considera usar un modelo de Ollama más pequeño:
```bash
ollama pull phi3:mini
# Y en config.ini: ollama_model = phi3:mini
```

## 🧪 5. Testing
Este proyecto incluye una suite de tests unitarios para asegurar la fiabilidad de sus componentes principales.

### Ejecutar los Tests
```bash
pip install -e .[test]
python3 -m pytest
```
