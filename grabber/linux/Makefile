build:
	gcc linux.c -o linux.so -O3 -lX11 -Wextra -Wl,-soname,linux -g -Og -shared -fPIC

clean:
	rm linux.so

test:
	gcc linux.c -o linux -O3 -lX11 -Wextra -Wl,-soname,linux -g -Og && ./linux

memcheck:
	gcc linux.c -o linux -O3 -lX11 -Wextra -Wl,-soname,linux -g -Og && valgrind --leak-check=full --show-reachable=yes ./linux
