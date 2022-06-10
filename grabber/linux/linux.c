#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <ctype.h>
#include <X11/X.h>
#include <X11/Xutil.h>

typedef struct
{
    Window window;
    char *name;
    float match;
} Match;

typedef struct
{
    Window window;
    char *name;
} Client;

typedef struct
{
    XImage *ximage;
    uint width;
    uint height;
} Image;

typedef struct
{
    int width;
    int height;
} Size;

float Similarity(char *str1, char *str2)
{
    size_t len1 = strlen(str1), len2 = strlen(str2);
    float lenLCS;
    unsigned j, k, *previous, *next;

    if (len1 == 0 || len2 == 0)
        return 0;

    previous = (unsigned *)calloc(len1 + 1, sizeof(unsigned));
    next = (unsigned *)calloc(len1 + 1, sizeof(unsigned));

    for (j = 0; j < len2; ++j)
    {
        for (k = 1; k <= len1; ++k)
        {
            if (str1[k - 1] == str2[j])
                next[k] = previous[k - 1] + 1;
            else
                next[k] = previous[k] >= next[k - 1] ? previous[k] : next[k - 1];
        }

        unsigned *temp = previous;
        previous = next;
        next = temp;
    }

    lenLCS = (float)previous[len1];

    free(previous);
    free(next);

    return lenLCS /= len1;
}

void SetErrorHandler(XErrorHandler handler)
{
    XSetErrorHandler(handler);
}

Display *GetDisplay()
{
    return XOpenDisplay(NULL);
}

void CloseDisplay(Display *display)
{
    XCloseDisplay(display);
}

char *GetWindowName(Display *display, Window window)
{
    Atom atom = XInternAtom(display, "_NET_WM_NAME", true);
    Atom type;
    int format;
    unsigned long nitems, bytes_after;
    unsigned char *data;

    int status = XGetWindowProperty(display, window, atom, 0, 1024, false, AnyPropertyType, &type, &format, &nitems, &bytes_after, &data);

    if (status != Success)
        return NULL;

    return (char *)data;
}

Window FindWindow(Display *display, const char *search_name)
{
    Window window = DefaultRootWindow(display);
    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);

    Atom type;
    int format;
    unsigned long n;
    unsigned long buf;
    unsigned char *data = 0;

    int status = XGetWindowProperty(
        display, window, atom, 0L, (~0L), 0, 0L, &type, &format, &n, &buf, &data);

    if (status >= Success && n)
    {
        Window *windows = (Window *)data;

        Match *matches;
        matches = (Match *)malloc(n * sizeof(Match));

        if (matches == NULL)
        {
            XFree(data);
            return 0;
        }

        // lowercase the query name
        char *search_name_lowercase = strdup(search_name);
        for (unsigned int i = 0; i < strlen(search_name_lowercase); i++)
            search_name_lowercase[i] = tolower(search_name_lowercase[i]);

        for (ulong i = 0; i < n; i++)
        {
            // get window
            matches[i].window = windows[i];

            // get window name
            char *window_name = GetWindowName(display, windows[i]);

            // lowercase the window name
            char *window_name_lowercase = strdup(window_name);
            for (uint j = 0; j < strlen(window_name_lowercase); j++)
                window_name_lowercase[j] = tolower(window_name_lowercase[j]);

            // calculate match
            if (window_name != NULL)
            {
                matches[i].name = window_name;
                matches[i].match = Similarity(search_name_lowercase, window_name_lowercase);
            }
            else
            {
                matches[i].name = "";
                matches[i].match = 0.0;
            }

            free(window_name_lowercase);
        }

        Match best_match;
        best_match.match = 0.0;

        // find best match
        for (unsigned long i = 0; i < n; i++)
        {
            if (matches[i].match > best_match.match)
                best_match = matches[i];
            free(matches[i].name);
        }

        // free memory
        free(matches);
        free(search_name_lowercase);
        XFree(data);

        // make sure we found a match by applying a threshold
        if (best_match.match > 0.9)
            return best_match.window;

        return 0;
    }

    // free memory
    XFree(data);
    return 0;
}

Window FindDesktop(Display *diplay)
{
    return XRootWindow(diplay, 0);
}

Image *GrabWindow(Display *display, Window window)
{
    XWindowAttributes attr;
    int status = XGetWindowAttributes(display, window, &attr);

    if (status == 0)
        return NULL;

    if (attr.map_state != IsViewable)
        return NULL;

    Image *image = (Image *)malloc(sizeof(Image));

    if (image == NULL)
        return NULL;

    image->width = attr.width;
    image->height = attr.height;
    image->ximage = XGetImage(display, window, 0, 0, attr.width, attr.height, AllPlanes, ZPixmap);

    return image;
}

Image *GrabRegion(Display *display, Window window, int x, int y, int width, int height)
{
    Image *image = (Image *)malloc(sizeof(Image));

    if (image == NULL)
        return NULL;

    image->width = width;
    image->height = height;
    image->ximage = XGetImage(display, window, x, y, width, height, AllPlanes, ZPixmap);
    return image;
}

void FreeImage(Image *image)
{
    XDestroyImage(image->ximage);
    free(image);
}

void FreeXImage(XImage *image)
{
    XDestroyImage(image);
}

Size *GetWindowSize(Display *display, Window window)
{
    XWindowAttributes attr;
    int status = XGetWindowAttributes(display, window, &attr);

    if (status != 1)
        return NULL;

    Size *size = (Size *)malloc(sizeof(Size));

    if (size == NULL)
        return NULL;

    size->width = attr.width;
    size->height = attr.height;

    return size;
}

void FreeWindowSize(Size *size)
{
    free(size);
}

Client *GetClientList(Display *display)
{
    Window root = DefaultRootWindow(display);
    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);
    Atom t;
    int f;
    ulong n;
    ulong b;
    unsigned char *data = 0;

    int status = XGetWindowProperty(display, root, atom, 0L, (~0L), 0, 0L, &t, &f, &n, &b, &data);

    if (status != Success || n == 0)
    {
        XFree(data);
        return NULL;
    }

    ulong *client_list = (ulong *)data;
    ulong numClients = n;
    Client *clients = malloc(sizeof(Client) * numClients);

    if (clients == NULL)
    {
        XFree(data);
        return NULL;
    }

    for (unsigned long i = 0; i < numClients; i++)
    {
        Window w = client_list[i];
        char *name = GetWindowName(display, w);

        clients[i].window = w;
        clients[i].name = name;
    }

    XFree(data);
    return clients;

}

uint GetClientCount(Display *display)
{
    Window root = DefaultRootWindow(display);
    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);
    Atom type;
    int format;
    ulong n;
    ulong buf;
    unsigned char *data = 0;

    int status = XGetWindowProperty(
        display, root, atom, 0L, (~0L), 0, 0L, &type, &format, &n, &buf, &data);

    XFree(data);

    if (status != Success)
        return 0;

    return n;
}

void FreeClientList(Client *clients, uint num_clients)
{
    for (uint i = 0; i < num_clients; i++)
        free(clients[i].name);

    free(clients);
}

int main()
{
    Display *display = GetDisplay();
    Window w = FindWindow(display, "chrome");

    if (w != 0)
    {
        char *name = GetWindowName(display, w);
        printf("window name is %s\n", name);

        int width, height;
        GetWindowSize(display, w);

        printf("window size is %d x %d\n", width, height);

        free(name);
    }
    else
    {
        printf("could not find window\n");
    }

    CloseDisplay(display);
    return 0;
}