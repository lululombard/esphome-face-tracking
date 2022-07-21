# ESPHome ESP32 Cam pan/tilt servo follow

:warning: This is not a finished product and probably will never be, it's an experiment to follow a face using an ESP32 running ESPHome with a camera and servos.

## How do I make this work?

This has only been tested on Linux (Ubuntu 20.04)

First, run `python3.10 -m venv env` to create a venv, then `source env/bin/activate` to activate it, `pip install -r requirements.txt` to install libraries, `cp .env.example .env` to copy the default config, then edit that `.env` file with your info, then you only need to run the tool using `python esphome_camera_tracking.py`.

PS: for better results, make sure to add `idle_framerate: 1 fps` to the config of your ESP32 Camera in ESPHome. You'll find my `office-fan.yaml` ESPHome config for the ESP32-CAM module.
