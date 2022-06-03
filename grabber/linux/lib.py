from typing import Tuple, List
import ctypes
import time
import os
import numpy as np
import cv2

from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_int,
    c_ubyte,
    c_ulong,
)


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


CFUNCTIONS = {
    "get_display": {
        "restype": POINTER(Display),
        "argtypes": [],
    },
    "close_display": {
        "restype": None,
        "argtypes": [POINTER(Display)],
    },
    "get_window_name": {
        "restype": c_char_p,
        "argtypes": [POINTER(Display), Window],
    },
    "find_window": {
        "restype": Window,
        "argtypes": [POINTER(Display), c_char_p],
    },
    "get_desktop": {
        "restype": Window,
        "argtypes": [POINTER(Display)],
    },
    "get_window_screen": {
        "restype": None,
        "argtypes": [
            POINTER(Display),
            Window,
            c_int,
            c_int,
            c_int,
            c_int,
            c_bool,
            POINTER(c_ubyte),
        ],
    },
    "get_window_size": {
        "restype": None,
        "argtypes": [POINTER(Display), Window, POINTER(c_int), POINTER(c_int)],
    },
    "get_client_list": {
        "restype": POINTER(Client),
        "argtypes": [POINTER(Display)],
    },
    "get_client_count": {
        "restype": c_int,
        "argtypes": [POINTER(Display)],
    },
    "free_client_list": {
        "restype": None,
        "argtypes": [POINTER(Client), c_ulong],
    },
}


class Grabber:
    """
    Class that handles the connection to the X server.
    It also contains all the functions that are used to interact with the X server.
    """

    def __init__(self) -> None:
        """
        Initialize the connection to the X server.
        """

        LIB = "linux.so"
        PATH = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LIB
        self.lib = ctypes.CDLL(PATH)

        # set the restype and argtypes for each function
        for func_name, func_info in CFUNCTIONS.items():
            func = getattr(self.lib, func_name)
            func.restype = func_info["restype"]
            func.argtypes = func_info["argtypes"]

        # get the display connection
        self.display = self.lib.get_display()
        self.window = self.lib.get_desktop(self.display)

        self.width = c_int()
        self.height = c_int()

        self.lib.get_window_size(
            self.display,
            self.window,
            self.width,
            self.height,
        )

        self.pixels = c_ubyte()

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
        self.lib.close_display(self.display)

    def get_client_list(self) -> List[Tuple[Window, str]]:
        """
        Get a list of all the clients that are currently open.
        """

        client_list = self.lib.get_client_list(self.display)
        client_count = self.lib.get_client_count(self.display)

        clients = []

        for i in range(client_count):
            clients.append((client_list[i].window, client_list[i].name.decode()))

        self.lib.free_client_list(client_list, client_count)
        return clients

    def get_window_name(self, window: int) -> str:
        """
        Get the name of the window.
        """

        try:
            name = self.lib.get_window_name(self.display, window).decode()
        except:
            name = ""
        return name

    def get_window_size(self, window: int) -> Tuple[int, int]:
        """
        Get the size (width, height) of the window.
        """

        self.lib.get_window_size(
            self.display,
            window,
            self.width,
            self.height,
        )
        return self.width.value, self.height.value

    def find_window(self, title: str) -> Window:
        """
        Find a window by its title.
        """

        return self.lib.find_window(self.display, title.encode())

    def get_desktop(self) -> Window:
        """
        Get the desktop window.
        """

        return self.lib.get_desktop(self.display)

    def get_window_screen(
        self, window: int, x: int, y: int, width: int, height: int, rbg: bool = False
    ) -> np.ndarray:
        """
        Get the screen of the window.
        """

        self.pixels = (c_ubyte * (width * height * 3))()
        self.lib.get_window_screen(
            self.display,
            window,
            x,
            y,
            width,
            height,
            rbg,
            self.pixels,
        )

        return np.frombuffer(self.pixels, dtype=np.uint8).reshape(height, width, 3)


def main() -> None:
    """
    Main function.
    """

    wm = Grabber()
    chrome = wm.find_window("chrome")

    prev_frame_time = 0
    new_frame_time = 0

    while True:

        width, height = wm.get_window_size(chrome)
        image = wm.get_window_screen(chrome, 0, 0, width, height, False) # bgr enabled du to opencv

        cv2.imshow("image", image)

        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

        print(int(fps))

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    main()
