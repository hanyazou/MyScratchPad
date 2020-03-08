#include <counter/counter.h>

#define billion (1000000000LL)  /* 1,000,000,000 < 1^32 = 4,294,967,296 */

struct counter {
    int initialized;
    uint32_t sdiv, smul;
    uint32_t nsdiv, nsmul;
    uint64_t mask;
    uint32_t freq;
};

static struct counter counter_cntvct_el0 = { 0 };

int
counter_init(void)
{
    struct counter *c = &counter_cntvct_el0;

    /* get clock frequency */
    counter_freq = get_cntfrq();
    c->freq= get_cntfrq();

    c->mask = ((1LL << 32) - 1);

    /*
     *
     */
    for (c->sdiv = 0; c->sdiv < 56; c->sdiv++) {
        uint64_t tmp;
        tmp = (1LL << c->sdiv)/c->freq;
        if ((1LL << 32) <= tmp)
            break;
    }
    c->sdiv -= 1;
    c->smul = (uint32_t)((1LL << c->sdiv)/c->freq);

    /*
     *
     */
    for (c->nsdiv = 0; c->nsdiv < 56; c->nsdiv++) {
        uint64_t tmp;
        tmp = (billion << c->nsdiv)/c->freq;
        if ((1LL << 32) <= tmp)
            break;
    }
    c->nsdiv -= 1;
    c->nsmul = (uint32_t)((billion << c->nsdiv)/c->freq);

    return (0);
}

void
counter_show_params(void)
{
    struct counter *c = &counter_cntvct_el0;

    printf("freq=%d\n", c->freq);
    printf("sec: mul=%u, div=%u\n", c->smul, c->sdiv);
    printf("nsec: mul=%u, div=%u\n", c->nsmul, c->nsdiv);
}

#undef billion

void
counter_to_timespec1(uint64_t vct, struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    struct counter *c = &counter_cntvct_el0;
    uint64_t hi, low;
    uint64_t sec, nsec;

    hi = (vct >> 32) * c->smul;
    low = (vct & c->mask) * c->smul;;
    sec = (hi >> (c->sdiv - 32)) + (low >> c->sdiv);
    nsec = (((vct - sec * c->freq) * c->nsmul) >> c->nsdiv);
    while (billion <= nsec) {
        sec++;
        nsec -= billion;
    }

    ts->tv_sec = sec;
    ts->tv_nsec = nsec;
}

void
counter_to_timespec2(uint64_t vct, struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    struct counter *c = &counter_cntvct_el0;

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;
}

void
counter_to_timespec3(uint64_t vct, struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    ts->tv_sec = vct / counter_freq;
    //ts->tv_nsec = (vct % counter_freq) * billion / counter_freq;
    ts->tv_nsec = (vct - ((vct / counter_freq) * counter_freq)) * billion / counter_freq;
}

void
counter_gettime1(struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    struct counter *c = &counter_cntvct_el0;
    uint64_t vct = get_cntvct();
    uint64_t hi, low;
    uint64_t sec, nsec;

    hi = (vct >> 32) * c->smul;
    low = (vct & c->mask) * c->smul;;
    sec = (hi >> (c->sdiv - 32)) + (low >> c->sdiv);
    nsec = (((vct - sec * c->freq) * c->nsmul) >> c->nsdiv);
    while (billion <= nsec) {
        sec++;
        nsec -= billion;
    }

    ts->tv_sec = sec;
    ts->tv_nsec = nsec;
}

void
counter_gettime2(struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    struct counter *c = &counter_cntvct_el0;
    uint64_t vct = get_cntvct();

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;
}
