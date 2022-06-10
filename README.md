# grabber
Python cross-plateform package to make screenshot from any window

```python
from grabber import Grabber
import cv2

grabber = Grabber()
chrome = grabber.find("chrome")

image = grabber.capture(chrome, format="bgr")

cv2.imshow("image", image)
cv2.waitKey(0)
 ```
