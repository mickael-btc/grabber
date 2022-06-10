from types import SimpleNamespace
from typing import Any, Callable, Optional, Tuple, List, Union
import ctypes
import time
import os
import numpy as np
import cv2
from PIL import Image

from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_float,
    c_int,
    c_uint,
    c_ubyte,
    c_ulong,
    c_void_p,
)

ERROR = SimpleNamespace(details={})

RGB = lambda image: cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
BGR = lambda image: cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
GRAY = lambda image: cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)


class Client(Structure):
    """
    Structure for the client list.
    """

    _fields_ = [
        ("window", ctypes.c_ulong),
        ("name", ctypes.c_char_p),
    ]


class Display(Structure):
    """
    Structure that serves as the connection to the X server
    and that contains all the information about that X server.
    """


class Window(c_ulong):
    """
    Structure that represents a window.
    """

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return str(self.value)


class XImage(Structure):
    """
    Description of an image as it exists in the client's memory.
    https://tronche.com/gui/x/xlib/graphics/images.html
    """

    _fields_ = [
        ("width", c_int),
        ("height", c_int),
        ("xoffset", c_int),
        ("format", c_int),
        ("data", c_void_p),
        ("byte_order", c_int),
        ("bitmap_unit", c_int),
        ("bitmap_bit_order", c_int),
        ("bitmap_pad", c_int),
        ("depth", c_int),
        ("bytes_per_line", c_int),
        ("bits_per_pixel", c_int),
        ("red_mask", c_ulong),
        ("green_mask", c_ulong),
        ("blue_mask", c_ulong),
    ]


class GImage(Structure):
    """
    Structure that represents an image.
    """

    _fields_ = [
        ("ximage", POINTER(XImage)),
        ("width", c_uint),
        ("height", c_uint),
    ]


class Size(Structure):
    """
    Structure that represents a size.
    """

    _fields_ = [
        ("width", c_int),
        ("height", c_int),
    ]


class Event(Structure):
    """
    XErrorEvent to debug eventual errors.
    https://tronche.com/gui/x/xlib/event-handling/protocol-errors/default-handlers.html
    """

    _fields_ = [
        ("type", c_int),
        ("display", POINTER(Display)),
        ("serial", c_ulong),
        ("error_code", c_ubyte),
        ("request_code", c_ubyte),
        ("minor_code", c_ubyte),
        ("resourceid", c_void_p),
    ]


CFUNCTIONS = {
    "SetErrorHandler": {
        "restype": None,
        "argtypes": [CFUNCTYPE(c_int, POINTER(Display), POINTER(Event))],
    },
    "Similarity": {
        "restype": c_float,
        "argtypes": [POINTER(c_char_p), POINTER(c_char_p)],
    },
    "GetDisplay": {
        "restype": POINTER(Display),
        "argtypes": [],
    },
    "CloseDisplay": {
        "restype": None,
        "argtypes": [POINTER(Display)],
    },
    "GetWindowName": {
        "restype": c_char_p,
        "argtypes": [POINTER(Display), Window],
    },
    "FindWindow": {
        "restype": Window,
        "argtypes": [POINTER(Display), c_char_p],
    },
    "FindDesktop": {
        "restype": Window,
        "argtypes": [POINTER(Display)],
    },
    "GrabWindow": {
        "restype": POINTER(GImage),
        "argtypes": [POINTER(Display), Window],
    },
    "GrabRegion": {
        "restype": POINTER(GImage),
        "argtypes": [POINTER(Display), Window, c_int, c_int, c_int, c_int],
    },
    "FreeImage": {
        "restype": None,
        "argtypes": [POINTER(GImage)],
    },
    "FreeXImage": {
        "restype": None,
        "argtypes": [POINTER(XImage)],
    },
    "GetWindowSize": {
        "restype": POINTER(Size),
        "argtypes": [POINTER(Display), Window],
    },
    "FreeWindowSize": {
        "restype": None,
        "argtypes": [POINTER(Size)],
    },
    "GetClientList": {
        "restype": POINTER(Client),
        "argtypes": [POINTER(Display)],
    },
    "GetClientCount": {
        "restype": c_uint,
        "argtypes": [POINTER(Display)],
    },
    "FreeClientList": {
        "restype": None,
        "argtypes": [POINTER(Client), c_uint],
    },
}


@CFUNCTYPE(c_int, POINTER(Display), POINTER(Event))
def error_handler(_, event):
    """Specifies the program's supplied error handler."""

    evt = event.contents
    ERROR.details = {
        "type": evt.type,
        "serial": evt.serial,
        "error_code": evt.error_code,
        "request_code": evt.request_code,
        "minor_code": evt.minor_code,
    }

    return 0


class GrabberError(Exception):
    """
    Exception for grabber errors.
    """

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details


class LibError(Exception):
    """
    Exception for lib errors.
    """

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details


class Grabber:
    """
    Class that handles the connection to the X server.
    It also contains all the functions that are used to interact with the X server.
    """

    def __init__(self, prevent_exception=True, debug=False) -> None:
        """
        Initialize the connection to the X server.
        """

        self.prevent_exception = prevent_exception

        # Load the custom library.
        LIB = "linux.so"
        PATH = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LIB
        self.lib = ctypes.CDLL(PATH)

        # set the restype and argtypes for each function
        for func_name, func_info in CFUNCTIONS.items():
            func = getattr(self.lib, func_name)
            func.restype = func_info["restype"]
            func.argtypes = func_info["argtypes"]
            func.errcheck = self.error_check

        # set the error handler
        self.lib.SetErrorHandler(error_handler)

        # get the display connection
        self.display = self.lib.GetDisplay()

        # to compute fps
        self._prev = 0
        self._curr = 0
        self.fps = 0

    def __enter__(self) -> "Grabber":
        """
        Enter the context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager.
        """
        self.stop()

    def __del__(self) -> None:
        """
        On deletion, free the resources.
        """
        self.stop()

    def stop(self) -> None:
        """
        Free the resources.
        """
        self.lib.CloseDisplay(self.display)

    def error_check(self, result: any, func: Callable, args: Tuple) -> Any:
        """
        Check for errors.
        """
        if ERROR.details:
            details = ERROR.details
            ERROR.details = {}

            raise LibError(
                f"Error in {func.__name__}",
                details,
            )

        return result

    def find_windows(self) -> List[Tuple[Window, str]]:
        """
        Get a list of all the windows that are currently open.
        """

        try:
            client_list = self.lib.GetClientList(self.display)
            client_count = self.lib.GetClientCount(self.display)

            clients = []

            for i in range(client_count):
                clients.append((client_list[i].window, client_list[i].name.decode()))

            self.lib.FreeClientList(client_list, client_count)
            return clients

        except (LibError, ValueError) as e:
            if self.prevent_exception:
                return []
            else:
                raise GrabberError(e)

    def get_name(self, window: Window) -> str:
        """
        Get the name of the window.
        """
        try:
            return self.lib.GetWindowName(self.display, window).decode()
        except (LibError, ValueError) as e:
            if self.prevent_exception:
                return None
            else:
                raise GrabberError(e)

    def get_size(self, window: Window) -> Tuple[int, int]:
        """
        Get the size (width, height) of the window.
        """

        try:
            size = self.lib.GetWindowSize(self.display, window)

            width = size.contents.width
            height = size.contents.height

            self.lib.FreeWindowSize(size)

            return width, height
        except (LibError, ValueError) as e:
            if self.prevent_exception:
                return None
            else:
                raise GrabberError(e)

    def find(self, title: Optional[str] = "") -> Window:
        """
        Find a window by its title. If no title is given, it will find the desktop window.
        """

        try:
            if title == "":
                window = self.lib.FindDesktop(self.display)
            else:
                window = self.lib.FindWindow(self.display, title.encode())
            return window
        except (LibError, ValueError) as e:
            if self.prevent_exception:
                return None
            else:
                raise GrabberError(e)

    def capture(
        self,
        window: Window,
        region: Optional[Tuple[int, int, int, int]] = None,
        format: Optional[str] = "rgb",
        type: Optional[str] = "cv2",
    ) -> Union[np.ndarray, Image.Image]:
        """
        Capture the window.

        :param window: The window handle to capture.
        :param region: The region to capture.
        :param format: The format of the image, either "rgb", "bgr" or "gray".
        :param type: The type of the image, either "cv2" (numpy) or "Image" (PIL).
        :return: The image as a numpy array or a PIL image.
        """

        self._curr = time.time()
        self.fps = 1 / (self._curr - self._prev)
        self._prev = self._curr

        try:
            if region is None:
                image = self.lib.GrabWindow(self.display, window)
            else:
                image = self.lib.GrabRegion(
                    self.display, window, region[0], region[1], region[2], region[3]
                )

            ximage = image.contents.ximage
            width = image.contents.width
            height = image.contents.height

            raw_data = ctypes.cast(
                ximage.contents.data,
                POINTER(c_ubyte * height * width * 4),
            )

            content = bytearray(raw_data.contents)
            self.lib.FreeImage(image)

            img = np.asarray(content).reshape(height, width, 4)

            if format == "rgb":
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            elif format == "bgr":
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif format == "gray":
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            else:
                raise GrabberError(f"Unknown format: {format}")

            if type == "cv2":
                return img
            elif type == "pil":
                return Image.fromarray(img)
            else:
                raise GrabberError(f"Unknown type: {type}")

        except (LibError, ValueError) as e:
            if self.prevent_exception:
                return None
            else:
                raise GrabberError(e)
