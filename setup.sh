#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing pygame..."
apt-get update
apt-get install -y python3-pygame
echo "pygame installed."

echo "Installing dependencies..."
apt-get install -y python3-pip python3-dev build-essential portaudio19-dev python3-pyaudio python3-scipy alsa-utils
python3 -m pip install --isolated --no-cache-dir --index-url https://pypi.org/simple -r "$SCRIPT_DIR/edge/requirements.txt"
echo "Dependencies installed."

apt-get install -y python3-matplotlib

echo "Installing test dependencies..."
python3 -m pip install --isolated --no-cache-dir --index-url https://pypi.org/simple pytest httpx fastapi uvicorn google-cloud-storage python-multipart faster-whisper

echo "Test dependencies installed."

# echo "Installing Google Cloud SDK..."
# curl https://sdk.cloud.google.com | bash -s -- --disable-prompts
# echo "Google Cloud SDK installed. Run 'gcloud auth application-default login' to authenticate."

export SDL_AUDIODRIVER=alsa

# Configure ALSA to use HDMI output (hw:1,3) as default, this is for the speaker audio output
echo "Configuring ALSA default output to HDMI (hw:1,3)..."
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type plug
    slave.pcm "hw:1,3"
}
ctl.!default {
    type hw
    card 1
}
EOF
echo "ALSA configured."