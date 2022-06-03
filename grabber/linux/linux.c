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

/*
    A function which returns how similar 2 strings are
    Assumes that both point to 2 valid null terminated array of chars.
    Returns the similarity between them as a float between 0 and 1.
*/
float similarity(char *str1, char *str2)
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

Display *get_display()
{
    return XOpenDisplay(NULL);
}

void close_display(Display *display)
{
    XCloseDisplay(display);
}

/*
    Get the window name
*/
char *get_window_name(Display *display, Window window)
{
    Atom atom = XInternAtom(display, "_NET_WM_NAME", true);

    Atom t;
    int f;

    unsigned long n;
    unsigned long b;
    unsigned char *data = 0;

    int status = XGetWindowProperty(display, window, atom, 0L, (~0L), false, AnyPropertyType, &t, &f, &n, &b, &data);

    if (status >= Success && n)
        return (char *)data;

    return NULL;
}

/*
    Find the window by name.
*/
Window find_window(Display *display, const char *search_name)
{
    Window window = DefaultRootWindow(display);
    // lowercase the name
    char *search_name_lowercase = strdup(search_name);
    for (unsigned int i = 0; i < strlen(search_name_lowercase); i++)
        search_name_lowercase[i] = tolower(search_name_lowercase[i]);

    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);

    Atom t;
    int f;
    unsigned long n;
    unsigned long b;
    unsigned char *data = 0;

    int status = XGetWindowProperty(display, window, atom, 0L, (~0L), false, AnyPropertyType, &t, &f, &n, &b, &data);

    if (status >= Success && n)
    {
        Window *windows = (Window *)data;

        Match *matches;
        matches = (Match *)malloc(n * sizeof(Match));

        if (matches == NULL)
        {
            free(search_name_lowercase);
            XFree(data);
            return 0;
        }

        for (unsigned long i = 0; i < n; i++)
        {
            // get window
            matches[i].window = windows[i];

            // get window name
            char *window_name = get_window_name(display, windows[i]);

            // lowercase the window name
            char *window_name_lowercase = strdup(window_name);
            for (unsigned int j = 0; j < strlen(window_name_lowercase); j++)
                window_name_lowercase[j] = tolower(window_name_lowercase[j]);

            // calculate match
            if (window_name != NULL)
            {
                matches[i].name = window_name;
                matches[i].match = similarity(search_name_lowercase, window_name_lowercase);
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
    free(search_name_lowercase);
    XFree(data);

    return 0;
}

Window get_desktop(Display *diplay)
{
    return XRootWindow(diplay, 0);
}

/*
    Make a ScreenShot of a window. The screenshot is saved in out_image.
*/
void get_window_screen(Display *display, Window window, const int x, const int y, const int width, const int height, bool rgb, /*out*/ unsigned char *out_image)
{

    XMapWindow(display, window);

    XImage *image = XGetImage(display, window, x, y, width, height, AllPlanes, ZPixmap);

    if (image == NULL)
        return; // safe exit

    unsigned long red_mask = image->red_mask;
    unsigned long green_mask = image->green_mask;
    unsigned long blue_mask = image->blue_mask;

    int i, j;
    int ii = 0;

    int rgb_blue_shift;
    int rgb_green_shift;
    int rgb_red_shift;

    if (rgb)
    {
        rgb_blue_shift = 2;
        rgb_green_shift = 1;
        rgb_red_shift = 0;
    }
    else // bgr
    {
        rgb_blue_shift = 0;
        rgb_green_shift = 1;
        rgb_red_shift = 2;
    }

    for (i = 0; i < height; i++)
    {
        for (j = 0; j < width; j++)
        {
            unsigned long pixel = XGetPixel(image, j, i);
            unsigned char blue = (pixel & blue_mask);
            unsigned char green = (pixel & green_mask) >> 8;
            unsigned char red = (pixel & red_mask) >> 16;

            out_image[ii + rgb_blue_shift] = blue;
            out_image[ii + rgb_green_shift] = green;
            out_image[ii + rgb_red_shift] = red;
            ii += 3;
        }
    }

    XDestroyImage(image);
}

/*
    Get the window's height and width.
*/
void get_window_size(Display *display, Window window, int *width, int *height)
{
    XWindowAttributes attr;
    XGetWindowAttributes(display, window, &attr);
    *width = attr.width;
    *height = attr.height;
}

/*
    Returns the list of all opened windows
*/
Client *get_client_list(Display *display)
{
    Window root = DefaultRootWindow(display);
    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);
    Atom t;
    int f;
    unsigned long n;
    unsigned long b;
    unsigned char *data = 0;

    int status = XGetWindowProperty(display, root, atom, 0L, (~0L), 0, AnyPropertyType, &t, &f, &n, &b, &data);

    if (status >= Success)
    {
        unsigned long *client_list = (unsigned long *)data;
        unsigned long numClients = n;

        Client *clients = malloc(sizeof(Client) * numClients);

        for (unsigned long i = 0; i < numClients; i++)
        {
            Window w = client_list[i];
            char *name = get_window_name(display, w);

            clients[i].window = w;
            clients[i].name = name;
        }

        XFree(data);
        return clients;
    }

    XFree(data);
    return NULL;
}

/*
    Returns the number of clients in the list
*/
int get_client_count(Display *display)
{
    Window root = DefaultRootWindow(display);

    Atom atom = XInternAtom(display, "_NET_CLIENT_LIST", true);
    Atom t;
    int f;

    unsigned long n;
    unsigned long b;
    unsigned char *data = 0;

    XGetWindowProperty(display, root, atom, 0L, (~0L), false, AnyPropertyType, &t, &f, &n, &b, &data);

    XFree(data);
    return n;
}

/*
    Free the memory allocated for the list of clients.
*/
void free_client_list(Client *clients, unsigned long num_clients)
{
    for (unsigned long i = 0; i < num_clients; i++)
        free(clients[i].name);
    free(clients);
}

int main()
{
    Display *display = get_display();
    Window w = find_window(display, "chrome");

    if (w != 0)
    {
        char *name = get_window_name(display, w);
        printf("window name is %s\n", name);

        unsigned char *image = malloc(3 * 1920 * 1080);
        get_window_screen(display, w, 0, 0, 1920, 1080, true, image);

        int width, height;
        get_window_size(display, w, &width, &height);

        printf("window size is %d x %d\n", width, height);

        free(name);
        free(image);
    }
    else
    {
        printf("could not find window\n");
    }

    close_display(display);
    return 0;
}