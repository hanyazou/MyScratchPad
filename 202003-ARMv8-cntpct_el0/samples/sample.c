#include <stdio.h>
#include <time.h>
#include <counter/counter.h>

int main(int ac, char *av[])
{
    struct timespec cts, rts, mts;

    counter_init();
    counter_gettime(&cts);

    clock_gettime(CLOCK_REALTIME, &rts);
    clock_gettime(CLOCK_MONOTONIC, &mts);

    printf("  counter: %12d.%06d\n", (int)cts.tv_sec, (int)cts.tv_nsec/1000);
    printf("monotoinc: %12d.%06d\n", (int)mts.tv_sec, (int)mts.tv_nsec/1000);
    printf(" realtime: %12d.%06d\n", (int)rts.tv_sec, (int)rts.tv_nsec/1000);
}
