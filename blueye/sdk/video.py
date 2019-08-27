import cv2


def get_image(**kwargs):
    url = """rtsp://%s:8554/test""" % kwargs['ip']
    vcap = cv2.VideoCapture(url)
    ret, frame = vcap.read()
    if not ret:
        print("Could not capture image")
    vcap.release()
    return frame


def save_image(**kwargs):
    frame = get_image(**kwargs)
    cv2.imwrite(kwargs['filename'], frame)
