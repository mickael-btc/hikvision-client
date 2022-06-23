import json
import os
import sys
import logging

SETTINGS = {
    "ip": "192.168.1.1",
    "http": "8080",
    "rtsp": "554",
    "server": "5000",
    "username": "username",
    "password": "password",
}

if not os.path.exists("settings.json"):
    logging.info("settings.json not found, creating default settings.json")

    with open("settings.json", "w") as f:
        f.write(json.dumps(SETTINGS, indent=4))

    logging.info("settings.json created")
    logging.info("Please edit settings.json and restart")

    sys.exit(0)

else:
    logging.info("settings.json found")

    with open("settings.json", "r") as f:
        try:
            SETTINGS = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            logging.error("settings.json is not valid json")
            sys.exit(1)
