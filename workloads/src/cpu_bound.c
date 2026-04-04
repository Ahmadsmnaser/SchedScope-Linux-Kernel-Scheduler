#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t keep_running = 1;

static void handle_signal(int signo)
{
	(void)signo;
	keep_running = 0;
}

static uint64_t monotonic_msec(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)ts.tv_nsec / 1000000ULL;
}

int main(int argc, char **argv)
{
	uint64_t duration_ms;
	uint64_t start_ms;
	volatile uint64_t sink = 0;

	if (argc != 2) {
		fprintf(stderr, "usage: %s <duration_ms>\n", argv[0]);
		return 1;
	}

	duration_ms = strtoull(argv[1], NULL, 10);
	if (duration_ms == 0) {
		fprintf(stderr, "duration_ms must be > 0\n");
		return 1;
	}

	signal(SIGINT, handle_signal);
	signal(SIGTERM, handle_signal);

	start_ms = monotonic_msec();
	while (keep_running && monotonic_msec() - start_ms < duration_ms) {
		sink += 3;
		sink ^= sink << 1;
		sink += 7;
	}

	if (sink == 0xdeadbeefULL)
		fprintf(stderr, "unreachable sink=%llu\n", (unsigned long long)sink);

	return 0;
}
