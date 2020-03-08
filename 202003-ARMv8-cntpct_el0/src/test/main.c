#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <counter/counter.h>

#define billion (1000000000LL)  /* < 1^32 = 4,294,967,296 */

int
printcomma2(char *bp, int64_t n)
{
    char *p = bp;
    if (n < 1000) {
        return sprintf(bp, "%d", (int)n);
    }
    p += printcomma2(p, n/1000);
    p += sprintf(p, ",%03d", (int)(n%1000));
    return p - bp;
}

char*
printcomma(int64_t n)
{
    static int indx = 0;
    static char buf[5][32];
    static char *bp;

    if (5 <= ++indx)
        indx = 0;
    bp = buf[indx];

    if (n < 0) {
        bp += sprintf(bp, "-");
        n = -n;
    }
    printcomma2(bp, n);
    return buf[indx];
}

int
main(int ac, char *av[])
{
    uint64_t vct;
    struct timespec sys_time;
    struct timespec c;
    struct timespec c1, c2;
    time_t tmp;
    char buf[32];

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

    int64_t nsdiff1 = 0;
    int64_t nsdiff2 = 0;
    int errcount1 = 0;
    int errcount2 = 0;

    while (1) {
        counter_gettime(&c);
        clock_gettime(CLOCK_REALTIME, &c1);
        clock_gettime(CLOCK_MONOTONIC_RAW, &c2);

        int64_t tdiff1 = (c.tv_sec - c1.tv_sec) * billion + c.tv_nsec - c1.tv_nsec;
        int64_t tdiff2 = (c.tv_sec - c2.tv_sec) * billion + c.tv_nsec - c2.tv_nsec;

        time(&tmp);
        ctime_r(&tmp, buf);
        if (buf[strlen(buf)-1] == '\n')
            buf[strlen(buf)-1] = '\0';
        printf("%s: %9u.%09u %14s (%d) %14s (%d)\n",
               buf,
               (int)c.tv_sec, (int)c.tv_nsec,
               printcomma(tdiff1 - nsdiff1), errcount1,
               printcomma(tdiff2 - nsdiff2), errcount2);
        if (tdiff1 - nsdiff1 < -billion || billion < tdiff1 - nsdiff1) {
            nsdiff1 = tdiff1;
            errcount1++;
        }
        if (tdiff2 - nsdiff2 < -billion || billion < tdiff2 - nsdiff2) {
            nsdiff2 = tdiff2;
            errcount2++;
        }
        sleep(300);
    }
}
