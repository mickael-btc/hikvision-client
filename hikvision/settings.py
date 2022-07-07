import json
import os
import sys
from .logger import logger

SETTINGS = {
    "ip": "192.168.1.1",
    "http-port": "8080",
    "rtsp-port": "554",
    "server-port": "5000",
    "username": "username",
    "password": "password",
    "channel": "2",
}

if not os.path.exists("settings.json"):
    logger.info("settings.json not found, creating default settings.json")

    with open("settings.json", "w") as f:
        f.write(json.dumps(SETTINGS, indent=4))

    logger.info("settings.json created")
    logger.info("Please edit settings.json and restart")

    sys.exit(0)

else:
    logger.info("settings.json found")

    with open("settings.json", "r") as f:
        try:
            SETTINGS = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            logger.error("settings.json is not valid json")
            sys.exit(1)
