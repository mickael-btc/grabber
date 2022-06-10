from grabber import Grabber
from PIL import Image
import cv2


def main():

    grabber = Grabber()

    ################ opencv example
    chrome = grabber.find("chrome")
    image = grabber.capture(chrome, format="bgr")  # type="cv2"

    cv2.imshow("image", image)
    cv2.waitKey(0)

    ################### PIL example
    vscode = grabber.find("vs code")
    image = grabber.capture(vscode, type="pil")  # format="rgb"

    image.show()


if __name__ == "__main__":
    main()
