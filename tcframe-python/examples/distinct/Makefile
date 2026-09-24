CC      = gcc
CFLAGS  = -O2 -Wall -o

all: solution_ac solution_tle solution_mle

solution_ac:  solution_ac.c
	$(CC) $(CFLAGS) $@ $<

solution_tle: solution_tle.c
	$(CC) $(CFLAGS) $@ $<

solution_mle: solution_mle.c
	$(CC) $(CFLAGS) $@ $<

clean:
	rm -f solution_ac solution_tle solution_mle

.PHONY: all clean
