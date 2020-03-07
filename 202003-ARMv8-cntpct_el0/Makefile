
OPTS=-O3

all: test

test: test.c counter.c counter.h
	gcc ${OPTS} test.c counter.c -o test

clean:
	rm -rf test
