#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing pygame..."
apt-get update
apt-get install -y python3-pygame
echo "pygame installed."

echo "Installing dependencies..."
apt-get install -y python3-pip python3-dev build-essential portaudio19-dev python3-pyaudio python3-scipy
python3 -m pip install --isolated --no-cache-dir --index-url https://pypi.org/simple -r "$SCRIPT_DIR/edge/requirements.txt"
echo "Dependencies installed."  

export SDL_AUDIODRIVER=alsa