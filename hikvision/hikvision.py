from logger import logger
from settings import SETTINGS
import requests
import xmltodict
from typing import List
import cv2
import numpy as np


class HikvisionCamera:
    def __init__(self, id, ip, port, name, username) -> None:
        self.id = id
        self.ip = ip
        self.port = port
        self.name = name
        self.username = username
        self.cap = None

    def __repr__(self) -> str:
        return "HikvisionCamera(id={}, ip={}, port={}, name={}, username={})".format(
            self.id, self.ip, self.port, self.name, self.username
        )

    def __str__(self) -> str:
        return "HikvisionCamera(id={}, ip={}, port={}, name={}, username={})".format(
            self.id, self.ip, self.port, self.name, self.username
        )

    @property
    def stream_url(self) -> str:
        return "rtsp://{}:{}@{}:{}/ISAPI/Streaming/channels/{}0{}".format(
            SETTINGS["username"],
            SETTINGS["password"],
            SETTINGS["ip"],
            SETTINGS["rtsp-port"],
            self.id,
            SETTINGS["channel"],
        )

    @property
    def api_url(self) -> str:
        return "http://{}:{}@{}:{}/ISAPI/Streaming/channels/{}0{}".format(
            SETTINGS["username"],
            SETTINGS["password"],
            SETTINGS["ip"],
            SETTINGS["http-port"],
            self.id,
            SETTINGS["channel"],
        )

    @property
    def is_online(self) -> bool:
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

    def init_capture(self) -> bool:
        self.cap = cv2.VideoCapture(self.stream_url)
        return self.cap.isOpened()

    def release_capture(self) -> None:
        if self.cap.isOpened():
            self.cap.release()

    @property
    def frame(self) -> np.ndarray:
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                logger.error("Error getting frame from {}".format(self.api_url))
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
        info = camera["sourceInputPortDescriptor"]
        hikvision_cameras.append(
            HikvisionCamera(
                camera["id"],
                info["ipAddress"],
                info["managePortNo"],
                camera["name"],
                info["userName"],
            )
        )

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


def get_camera_by_ip(ip: str) -> HikvisionCamera:
    """
    Get camera by ip
    """
    cameras = get_cameras()

    for camera in cameras:
        if camera.ip == ip:
            return camera

    return None


def get_available_cameras() -> List[HikvisionCamera]:
    """
    Get all cameras that are online
    """
    cameras = get_cameras()

    available_cameras = []

    for camera in cameras:
        if camera.is_online:
            available_cameras.append(camera)

    return available_cameras


if __name__ == "__main__":
    cameras = get_available_cameras()

    for camera in cameras:
        print(camera)
        camera.init_capture()
        logger.info("Camera {} is online ({})".format(camera.id, camera.name))

        while True:
            image = camera.frame
            if image is not None:
                cv2.imshow("image", image)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        
        camera.release_capture()
        cv2.destroyAllWindows()
