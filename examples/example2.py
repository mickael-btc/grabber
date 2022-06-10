from grabber import Grabber


def main():

    grabber = Grabber()
    windows = grabber.find_windows()

    for window in windows:
        xid = window[0]
        title = window[1]
        width, height = grabber.get_size(xid)

        print(xid, title, (width, height))


if __name__ == "__main__":
    main()
