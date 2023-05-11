# grabber
Python linux package to make screenshot from any window

```python
from grabber import Grabber
import cv2

grabber = Grabber()

################ opencv example
chrome = grabber.find("chrome")
image = grabber.capture(chrome, format="bgr") # type="cv2"

cv2.imshow("image", image)
cv2.waitKey(0)

################### PIL example
vscode = grabber.find("vs code")
image = grabber.capture(vscode, type="pil") # format="rgb"

image.show()
 ```
