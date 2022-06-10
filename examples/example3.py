from grabber import Grabber
import cv2


def main():
    grabber = Grabber()
    desktop = grabber.find()

    while True:

        image = grabber.capture(desktop, format="bgr")
        image = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)

        cv2.imshow("image", image)
        print(grabber.fps)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    main()
