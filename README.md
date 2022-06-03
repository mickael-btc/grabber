# grabber
Python cross-plateform package to make screenshot from any window

```python
from grabber import grabber
import cv2
import time

def main() -> None:
    """
    Main function.
    """

    wm = grabber()
    chrome = wm.find_window("chrome")

    prev_frame_time = 0
    new_frame_time = 0

    while True:

        width, height = wm.get_window_size(chrome)
        image = wm.get_window_screen(chrome, 0, 0, width, height, False) # bgr enabled du to opencv

        # make cv2 imshow smaller to fit on screen
        image = cv2.resize(image, (0,0), fx=0.5, fy=0.5)

        cv2.imshow("image", image)

        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

        # print(int(fps))

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    main()
 ```
