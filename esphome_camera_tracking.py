
#!/usr/bin/env python3
import asyncio
import io
import os
import time

import aioesphomeapi
import numpy as np
from dotenv import load_dotenv
import face_recognition
from PIL import Image
from retry import retry

load_dotenv()

api = None
pan = None
tilt = None
pan_value = 0
tilt_value = 0
old_pan_value = 0
old_tilt_value = 0
last_state_update = time.time()

def handle_new_state(state):
    global last_state_update, api, pan, tilt, pan_value, tilt_value, old_pan_value, old_tilt_value

    last_state_update = time.time()

    if type(state) == aioesphomeapi.NumberState:
        if state.key == pan.key:
            pan_value = state.state
        if state.key == tilt.key:
            tilt_value = state.state

    if type(state) == aioesphomeapi.CameraState:
        try:
            # Save image
            with open("out.jpg", "wb") as f:
                f.write(state.data)

            image = np.array(Image.open(io.BytesIO(state.data)).convert('L'))
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) > 0:
                top, right, bottom, left = face_locations[0]

                x = (left + right) // 2
                y = (top + bottom) // 2

                x_offset = x - image.shape[1] // 2
                y_offset = y - image.shape[0] // 2

                x_offset_percent = x_offset * 100 // (image.shape[1] // 2)
                y_offset_percent = y_offset * 100 // (image.shape[0] // 2)

                pan_value -= x_offset_percent // 10

                tilt_value += y_offset_percent // 15

                if pan_value < pan.min_value:
                    pan_value = pan.min_value

                if pan_value > pan.max_value:
                    pan_value = pan.max_value

                if tilt_value < tilt.min_value:
                    tilt_value = tilt.min_value

                if tilt_value > tilt.max_value:
                    tilt_value = tilt.max_value

                if pan_value != old_pan_value:
                    old_pan_value = pan_value
                    asyncio.get_event_loop().create_task(api.number_command(pan.key, pan_value))

                if tilt_value != old_tilt_value:
                    old_tilt_value = tilt_value
                    asyncio.get_event_loop().create_task(api.number_command(tilt.key, tilt_value))

                print("Pan {} Tilt {}".format(pan_value, tilt_value))
        except Exception as e:
            print(e)

@retry(tries=3, delay=1, backoff=2)
async def main():
    global last_state_update, api, pan, tilt
    api = aioesphomeapi.APIClient(os.environ.get("ESP_IP"), int(os.environ.get("ESP_PORT")), '')

    print("Connecting to ESPHome API...")
    await api.connect(login=True)
    print("Connected to ESPHome API")

    entities = await api.list_entities_services()

    led = None

    for entity in entities[0]:
        if entity.object_id == os.environ.get("PAN_ENTITY"):
            pan = entity
        if entity.object_id == os.environ.get("TILT_ENTITY"):
            tilt = entity
        if type(entity) == aioesphomeapi.LightInfo:
            led = entity

    if not pan or not tilt:
        raise ValueError("pan or tilt entity not found, check PAN_ENTITY and TILT_ENTITY config")

    if led:
        await api.light_command(led.key, True)
        await asyncio.sleep(0.05)
        await api.light_command(led.key, False)

    await api.subscribe_states(handle_new_state)

    # Check if we have a state update in the last 15 seconds
    while True:
        if last_state_update + 15 < time.time():
            print("No state update in last 15 seconds, there must be a problem")
            last_state_update = time.time()
            break
        else:
            await asyncio.sleep(1)


@retry(aioesphomeapi.core.SocketAPIError, tries=10, delay=1, backoff=2)
def run():
    asyncio.run(main())

while True:
    run()
