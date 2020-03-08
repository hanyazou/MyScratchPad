#include <counter/counter.h>
#include <counter_priv.h>
#include <counter_test.h>

void
counter_to_timespec1(uint64_t vct, struct timespec *ts)
{
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
    struct counter *c = &counter_cntvct_el0;

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;
}

int
counter_gettime3(struct timespec *ts)
{
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

    return (0);
}

int
counter_gettime4(struct timespec *ts)
{
    struct counter *c = &counter_cntvct_el0;
    uint64_t vct = get_cntvct();

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;

    return (0);
}
