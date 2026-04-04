#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t keep_running = 1;

static void handle_signal(int signo)
{
	(void)signo;
	keep_running = 0;
}

static void sleep_msec(uint64_t msec)
{
	struct timespec req;

	req.tv_sec = (time_t)(msec / 1000ULL);
	req.tv_nsec = (long)((msec % 1000ULL) * 1000000ULL);

	while (nanosleep(&req, &req) == -1 && errno == EINTR && keep_running) {
	}
}

static void busy_msec(uint64_t msec)
{
	struct timespec ts;
	uint64_t start_ms;
	volatile uint64_t sink = 0;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	start_ms = (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)ts.tv_nsec / 1000000ULL;

	while (keep_running) {
		uint64_t now_ms;

		sink += 5;
		sink ^= sink << 2;

		clock_gettime(CLOCK_MONOTONIC, &ts);
		now_ms = (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)ts.tv_nsec / 1000000ULL;
		if (now_ms - start_ms >= msec)
			break;
	}

	if (sink == 0xabcdefULL)
		fprintf(stderr, "unreachable sink=%llu\n", (unsigned long long)sink);
}

int main(int argc, char **argv)
{
	uint64_t burst_ms;
	uint64_t sleep_ms;
	uint64_t cycles;
	uint64_t i;

	if (argc != 4) {
		fprintf(stderr, "usage: %s <burst_ms> <sleep_ms> <cycles>\n", argv[0]);
		return 1;
	}

	burst_ms = strtoull(argv[1], NULL, 10);
	sleep_ms = strtoull(argv[2], NULL, 10);
	cycles = strtoull(argv[3], NULL, 10);
	if (burst_ms == 0 || cycles == 0) {
		fprintf(stderr, "burst_ms and cycles must be > 0\n");
		return 1;
	}

	signal(SIGINT, handle_signal);
	signal(SIGTERM, handle_signal);

	for (i = 0; i < cycles && keep_running; ++i) {
		busy_msec(burst_ms);
		if (sleep_ms > 0 && keep_running)
			sleep_msec(sleep_ms);
	}

	return 0;
}
