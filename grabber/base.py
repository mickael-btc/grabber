from sys import platform


def Grabber(
    prevent_exception=True,
    debug=False,
):
    if platform == "linux" or platform == "linux2":
        from grabber.linux import Grabber as G

        return G(
            prevent_exception=prevent_exception,
            debug=debug,
        )

    else:
        raise Exception("Unsupported platform: " + platform)
