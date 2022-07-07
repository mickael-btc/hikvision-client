import cv2
import numpy as np
from hikvision.camera import get_available_cameras
from hikvision.logger import logger

def get_output_layers(net):
    """
    Get output layers from network
    """
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
    return ln

def main_control_loop() -> None:
    """
    Main control loop
    """
    # init nn
    net = cv2.dnn.readNetFromDarknet('./yolo/yolo.cfg', './yolo/yolo.weights')
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

    classes = open('./yolo/coco.names').read().strip().split('\n')
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(classes), 3), dtype="uint8")

    # init camera
    cameras = get_available_cameras()
    for camera in cameras:
        # camera.init_capture()
        camera.init_stream()
        logger.info("{} initialized".format(camera.name))

    while True:
        for camera in cameras:
            frame = camera.frame
            if frame is not None:
                
                image = cv2.resize(frame, (320, 320))
                blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (320, 320), (0, 0, 0), True, False)
                net.setInput(blob)
                outputs = net.forward(get_output_layers(net))

                boxes = []
                confidences = []
                classIDs = []
                h, w = image.shape[:2]
                
                detect = True

                if detect:

                    for output in outputs:
                        for detection in output:
                            scores = detection[5:]
                            classID = np.argmax(scores)
                            confidence = scores[classID]
                            if confidence > 0.5:
                                box = detection[0:4] * np.array([w, h, w, h])
                                centerX, centerY, width, height = box.astype('int')
                                x = int(centerX - (width / 2))
                                y = int(centerY - (height / 2))
                                boxes.append([x, y, int(width), int(height)])
                                confidences.append(float(confidence))
                                classIDs.append(classID)

                    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
                    if len(indices) > 0:
                        for i in indices.flatten():
                            (x, y) = (boxes[i][0], boxes[i][1])
                            (w, h) = (boxes[i][2], boxes[i][3])
                            red = (0, 0, 255)
                            cv2.rectangle(image, (x, y), (x + w, y + h), red, 2)
                            text = "{}: {:.4f}".format(classes[classIDs[i]], confidences[i])
                            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red, 1)



                cv2.imshow(camera.name, image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            logger.info("Quitting")
            for camera in cameras:
                camera.release_stream()
                logger.info("Camera {} released".format(camera.id))
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main_control_loop()
