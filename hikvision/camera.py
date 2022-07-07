from .logger import logger
from .settings import SETTINGS
import requests
import xmltodict
from typing import List
import cv2
import numpy as np
import threading
import queue
import time


class HikvisionCamera:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name
        self.cap = None
        self.flag = False
        self.stream_url = "rtsp://{}:{}@{}:{}/ISAPI/Streaming/channels/{}0{}".format(
            SETTINGS["username"],
            SETTINGS["password"],
            SETTINGS["ip"],
            SETTINGS["rtsp-port"],
            id,
            SETTINGS["channel"],
        )
        self.api_url = "http://{}:{}@{}:{}/ISAPI/Streaming/channels/{}0{}".format(
            SETTINGS["username"],
            SETTINGS["password"],
            SETTINGS["ip"],
            SETTINGS["http-port"],
            id,
            SETTINGS["channel"],
        )

    def __repr__(self) -> str:
        return "HikvisionCamera(id={}, ip={}, port={}, name={}, username={})".format(
            self.id, self.ip, self.port, self.name, self.username
        )

    def __str__(self) -> str:
        return "HikvisionCamera(id={}, ip={}, port={}, name={}, username={})".format(
            self.id, self.ip, self.port, self.name, self.username
        )

    @property
    def online(self) -> bool:
        try:
            response = requests.get(self.api_url)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return False

    @property
    def picture(self) -> np.ndarray:
        try:
            response = requests.get(self.api_url + "/picture")
            if response.status_code == 200:
                return cv2.imdecode(
                    np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR
                )
            else:
                logger.error("Error getting image from {}".format(self.api_url))
                return None
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return None

    def init_stream(self) -> bool:
        if self.cap is None:
            self.flag = True
            self.cap = cv2.VideoCapture(self.stream_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            self.q = queue.Queue()
            self.t = threading.Thread(target=self._stream_thread)
            self.t.daemon = True
            self.t.start()

    def release_stream(self) -> None:
        self.flag = False
        self.t.join()
        self.q.put(None)
        if self.cap.isOpened():
            self.cap.release()

    def _stream_thread(self) -> None:
        while self.flag and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Error getting frame from {}".format(self.api_url))
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    @property
    def frame(self) -> np.ndarray:
        if self.cap.isOpened():
            try:
                return self.q.get_nowait()
            except queue.Empty:
                return None
        else:
            logger.error("Camera {} is not initialized".format(self.id))
            return None


def get_cameras() -> List[HikvisionCamera]:
    """
    Get all cameras from the hikvision server
    """
    url = "http://{}:{}@{}:{}/ISAPI/ContentMgmt/InputProxy/channels".format(
        SETTINGS["username"],
        SETTINGS["password"],
        SETTINGS["ip"],
        SETTINGS["http-port"],
    )

    response = requests.get(url)

    if response.status_code != 200:
        logger.error("Failed to get cameras")
        return None

    xml = response.text

    try:
        data = xmltodict.parse(xml)
        cameras = data["InputProxyChannelList"]["InputProxyChannel"]
    except Exception as e:
        logger.error("Failed to parse xml")
        cameras = []
        return cameras

    hikvision_cameras = []

    for camera in cameras:
        id = int(camera["id"])
        name = camera["name"]
        hikvision_cameras.append(HikvisionCamera(id, name))

    return hikvision_cameras


def get_camera_by_id(id: int) -> HikvisionCamera:
    """
    Get camera by id
    """
    cameras = get_cameras()

    for camera in cameras:
        if camera.id == id:
            return camera

    return None


def get_camera_by_name(name: str) -> HikvisionCamera:
    """
    Get camera by name
    """
    cameras = get_cameras()

    for camera in cameras:
        if camera.name == name:
            return camera

    return None


def get_available_cameras() -> List[HikvisionCamera]:
    """
    Get all cameras that are online
    """
    cameras = get_cameras()

    available_cameras = []

    for camera in cameras:
        if camera.online:
            available_cameras.append(camera)

    return available_cameras
