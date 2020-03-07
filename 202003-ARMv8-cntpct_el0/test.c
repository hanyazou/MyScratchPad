#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <time.h>

static inline
uint64_t get_cntfrq(void)
{
    uint64_t cv;
    asm("isb");
    asm volatile("mrs %0, cntfrq_el0" : "=r" (cv));
    return cv;
 }

static inline
uint64_t get_cntvct(void)
{
    uint64_t cv;
    asm("isb");
    asm volatile("mrs %0, cntvct_el0" : "=r" (cv));
    return cv;
}

#define billion (1000000000LL)  /* < 1^32 = 4,294,967,296 */

int
main(int ac, char *av[])
{
    uint32_t sdiv, smul;
    uint32_t nsdiv, nsmul;
    uint64_t mask = ((1LL << 32) - 1);
    uint32_t freq;
    struct timespec ts;
    int64_t nsdiff;

    /*
     *
     */
    printf ("sizeof timespec.tv_sec is: %ld\n", sizeof(ts.tv_sec));
    printf ("sizeof timespec.tv_nsec is: %ld\n", sizeof(ts.tv_nsec));
    printf ("sizeof time_t is: %ld\n", sizeof(time_t));

    /* get clock frequency */
    freq= get_cntfrq();
    printf("freq=%d\n", freq);

    /*
     *
     */
    for (sdiv = 0; sdiv < 56; sdiv++) {
        uint64_t tmp;
        tmp = (1LL << sdiv)/freq;
        if ((1LL << 32) <= tmp)
            break;
    }
    sdiv -= 1;
    smul = (uint32_t)((1LL << sdiv)/freq);
    printf("sec: mul=%u, div=%u\n", smul, sdiv);

    /*
     *
     */
    for (nsdiv = 0; nsdiv < 56; nsdiv++) {
        uint64_t tmp;
        tmp = (billion << nsdiv)/freq;
        if ((1LL << 32) <= tmp)
            break;
    }
    nsdiv -= 1;
    nsmul = (uint32_t)((billion << nsdiv)/freq);
    printf("nsec: mul=%u, div=%u\n", nsmul, nsdiv);

    nsdiff = 0;
    while (1) {
        clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
        uint64_t vct = get_cntvct();
        //printf("vct=%ld\n", vct);

        uint64_t hi, low;
        uint64_t sec, nsec;
        hi = (vct >> 32) * smul;
        low = (vct & mask) * smul;;
        sec = (hi >> (sdiv - 32)) + (low >> sdiv);
        nsec = (((vct - sec * freq) * nsmul) >> nsdiv);
        while (billion <= nsec) {
            sec++;
            nsec -= billion;
        }

        uint64_t c_sec, c_nsec;
        c_sec = vct / freq;
        c_nsec = (vct - c_sec * freq) * billion / freq;

        int64_t tdiff = (sec - ts.tv_sec) * billion + nsec - ts.tv_nsec;

        printf("%9u.%09u %2d %2d %3d\n", (int)sec, (int)nsec,
               (int)(sec - c_sec), (int)(nsec - c_nsec),
               (int)(tdiff - nsdiff));
        if (tdiff - nsdiff < -billion || billion < tdiff - nsdiff)
            nsdiff = tdiff;
        sleep(1);
    }
}
