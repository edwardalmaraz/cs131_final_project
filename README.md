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

First, clone the `dance dance kareoke` repo 

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

```bash
# TODO - ANDY
```
---
