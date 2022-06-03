from sys import platform

def grabber():
    if platform == "linux" or platform == "linux2":
        from grabber.linux import Grabber
        return Grabber()

    else:
        raise Exception("Unsupported platform: " + platform)


