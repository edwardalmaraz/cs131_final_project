# Dance Dance Karaoke
> A Low-Cost, Open-Source Edge Platform for Real-Time Karaoke & Dance

> Edge Computing (CS131 Final Project)
---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Repository Structure](#repository-structure)
- [Setup & Installation](#setup--installation)
---

## Overview

**Dance Dance Karaoke** is an open-source dance and karaoke machine that uses the Jetson Nano as the edge device and utilizes GCP as the cloud platform. Our system enables real-time dance and karaoke gameplay, in which users must perform a sequence of poses displayed. In addition, our system plays music and displays lyrics in real time. We then perform pose, lyric, and pitch comparisons during post-processing, returning a total score to the user for each song. Our system is also designed to stay up to date with the most popular songs and dance choreographies. This allows the edge device to select songs from an expanding catalog. Finally, we host a leaderboard that lets users compare their scores with those of other players. Our distributed edge system was tested with two Jetson Nanos; however, its dynamic scalability enables multiple clients to play simultaneously. 

---
[DDK-Poster.pdf](https://github.com/user-attachments/files/28656897/DDK.3.pdf)

<img width="898" height="676" alt="Screenshot 2026-06-05 at 4 52 36 PM" src="https://github.com/user-attachments/assets/b36ed05e-d1fb-40d0-af41-387d8df901f9" />

---

## Features

- [ ] Real-time pose estimation via PoseNet
- [ ] Vocal pitch detection
- [ ] Speech transcription using Whisper
- [ ] Cloud-side library and scoring with feedback via GCP
- [ ] Scalable cloud design, enables dynamic client configurations

---

## Hardware Requirements

| Component      | Description                        |
|----------------|------------------------------------|
| Edge Device    | NVIDIA Jetson Nano                |
| Camera         | Logitech Webcam                    |
| Microphone     | Wireless microphone                |

---

## Software Requirements

| Dependency          | Purpose                          |
|---------------------|----------------------------------|
| PoseNet             | Pose estimation (submodule)      |
| Whisper             | Speech-to-text transcription     |
| FastAPI / Uvicorn   | Cloud API server                 |
| Google Cloud Storage| Cloud data/results storage       |
| pygame              | Audio/display on edge            |
| portaudio / pyaudio | Microphone input                 |

See `edge/requirements.txt` for the full edge dependency list.

---

## Repository Structure

```
cs131_final_project/
├── cloud/          # GCP backend — scoring logic, API endpoints
├── edge/           # Jetson Nano code — pose estimation, audio capture
├── posenet/        # PoseNet submodule 
├── Final Report/   # Final Report
├── setup.sh        # Automated setup script for edge device dependencies
├── .gitmodules
└── README.md
```
---

## Setup & Installation

### Clone the repos (with submodules)

First, clone the `dance dance karaoke` repo 

```bash
git clone --recurse-submodules https://github.com/edwardalmaraz/cs131_final_project.git
```

Next, we need to clone Nvidia's `jetson-inference` repo, which contains the necessary Docker image to run the PoseNet model. 
The entire system will run inside this Docker container. 
Follow the instructions on `jetson-inference` to get started with Docker. 

```bash
git clone --recurse-submodules https://github.com/dusty-nv/jetson-inference.git
```

### Edge Device Setup (Jetson Nano)

Once inside your Docker:
```bash
./setup.sh # wait for dependencies to install
```

This installs pygame, PyAudio, portaudio, and all Python dependencies from `edge/requirements.txt`, and configures ALSA audio output.

Start the application: 
```bash
cd edge/front-end/
python3 main.py
```

**NOTE:** Proper startup requires that you properly configure the audio inputs/outputs and camera to work inside of the Docker Container

### Cloud Setup (GCP)

The cloud backend is a **FastAPI** app (`cloud/main.py`) deployed to **Google Cloud Run**. It uses two **Google Cloud Storage** buckets:

- `cs131_song_bucket` — stores all things song related (`audio.mp3`, `vocals.wav`, `lyrics.txt`, `metadata.json`).
- `cs131_leaderboard_bucket` — stores leaderboard JSONs for each song.

Both bucket names are hardcoded in `cloud/database.py`. You need to change the names in your own GCP project, just be sure to have two buckets ready for storage.

Run all commands from the `cloud/` directory.

#### 0. Prerequisites
- A GCP project, ours is `cs131-project-495722`
- `gcloud` CLI installed and in your PATH
- Docker installed

#### 1. Authenticate and select your project
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-west1
```

#### 2. Enable required APIs
These are needed to be able to run the needed APIs using GCP
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com
```

#### 3. Create the two GCS buckets

Create both buckets from the Cloud Storage Console website under your newly made project:

1. Click **Create**, name the bucket `YOUR_SONG_BUCKET`, set **Location** to `us-west1` (single region), and leave the rest as defaults.
2. Repeat for `YOUR_LEADERBOARD_BUCKET`.
3. For each bucket, grant the Cloud Run service account read/write access: open the bucket → **Permissions** → **Grant Access** → add the default compute service account (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) with the **Storage Object Admin** role.

> GCS bucket names must be globally unique. Be sure the URLS on `cloud/database.py` (lines 8–9) match with the buckets you made on your GCP project page. 
#### 4. Deploy

Let google Cloud Build build the container:
```bash
gcloud run deploy YOUR-PROJECT-NAME\
  --source . \
  --region us-west1 \
  --allow-unauthenticated
```

#### 5. Verify the deployment
```bash
curl https://YOUR_CLOUD_RUN_URL/ping
# Expected: {"status": "online"}

curl https://YOUR_CLOUD_RUN_URL/songs
# Expected: {"songs": [...]}
```

#### 6. Point the edge client at your URL
Update `edge/front-end/cloud_api.py` (line 3) to your own google cloud project URL.
```python
API_BASE_URL = "https://YOUR_CLOUD_RUN_URL"
```
