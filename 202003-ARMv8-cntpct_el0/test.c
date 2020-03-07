#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include "counter.h"

#define billion (1000000000LL)  /* < 1^32 = 4,294,967,296 */

int
main(int ac, char *av[])
{
    uint64_t vct;
    struct timespec sys_time;
    struct timespec c;
    struct timespec c2;
    time_t tmp;

    counter_init();
    counter_show_params();

    vct = get_cntvct();
    counter_to_timespec(vct, &c);
    tmp = c.tv_sec;
    while (tmp == c.tv_sec) {
        vct = get_cntvct();
        counter_to_timespec(vct, &c);
    }

    {
        int i, test_case;
        int iteration = 100000000;  // 100,000,000
        volatile uint64_t vct;
        struct timespec st, et;
        char *test_desc;
        uint32_t duration;
            
        for (test_case = 0; test_case <= 7; test_case++) {
            clock_gettime(CLOCK_REALTIME, &st);
            switch (test_case) {
            case 0:
                test_desc = "  call counter_to_timespec1() w/o div";
                for (i = 0; i < iteration; i++) {
                    vct = get_cntvct();
                    counter_to_timespec1(vct, &c);
                }
                break;
            case 1:
                test_desc = "  call counter_to_timespec2() with div";
                for (i = 0; i < iteration; i++) {
                    vct = get_cntvct();
                    counter_to_timespec2(vct, &c);
                }
                break;
            case 2:
                test_desc = "  call counter_to_timespec2() with div w/o struct";
                for (i = 0; i < iteration; i++) {
                    vct = get_cntvct();
                    counter_to_timespec3(vct, &c);
                }
                break;
            case 3:
                test_desc = "inline counter_to_timespec4() w/o initialization";
                for (i = 0; i < iteration; i++) {
                    vct = get_cntvct();
                    counter_to_timespec4(vct, &c);
                }
                break;
            case 4:
                test_desc = "inline counter_to_timespec() with div";
                for (i = 0; i < iteration; i++) {
                    vct = get_cntvct();
                    counter_to_timespec(vct, &c);
                }
                break;
            case 5:
                test_desc = "inline counter_gettime() w/o initialization";
                for (i = 0; i < iteration; i++) {
                    counter_gettime(&c);
                }
                break;
            case 6:
                test_desc = "  call counter_gettime1() w/o div";
                for (i = 0; i < iteration; i++) {
                    counter_gettime1(&c);
                }
                break;
            case 7:
                test_desc = "  call counter_gettime1() with div";
                for (i = 0; i < iteration; i++) {
                    counter_gettime2(&c);
                }
                break;
            }
            clock_gettime(CLOCK_REALTIME, &et);
            duration = ((et.tv_sec * 1000000 + et.tv_nsec / 1000) -
                        (st.tv_sec * 1000000 + st.tv_nsec / 1000));
            printf("%d: %8.3f sec (%3d nsec) %s\n", test_case, (double)duration / 1000000,
                   duration / (iteration / 1000), test_desc);
        }
    }

    int64_t nsdiff;
    int errcount = 0;
    nsdiff = 0;
    while (1) {
        clock_gettime(CLOCK_MONOTONIC_RAW, &sys_time);
        vct = get_cntvct();
        counter_to_timespec(vct, &c);
        counter_to_timespec1(vct, &c2);

        int64_t tdiff = (c.tv_sec - sys_time.tv_sec) * billion + c.tv_nsec - sys_time.tv_nsec;

        printf("%9u.%09u %2d %3d %4d %d\n", (int)c.tv_sec, (int)c.tv_nsec,
               (int)(c.tv_sec - c2.tv_sec), (int)(c.tv_nsec - c2.tv_nsec),
               (int)(tdiff - nsdiff), errcount);
        if (tdiff - nsdiff < -billion || billion < tdiff - nsdiff) {
            nsdiff = tdiff;
            errcount++;
        }
        sleep(1);
    }
}
