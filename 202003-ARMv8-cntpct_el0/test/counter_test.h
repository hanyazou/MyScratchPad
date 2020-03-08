#ifndef COUNTER_COUNTER_TEST_H
#define COUNTER_COUNTER_TEST_H

#ifdef __cplusplus
extern "C" {
#endif

void counter_to_timespec1(uint64_t vct, struct timespec *ts);
void counter_to_timespec2(uint64_t vct, struct timespec *ts);

static inline void
counter_to_timespec3(uint64_t vct, struct timespec *ts)
{
    uint32_t freq = get_cntfrq();
    ts->tv_sec = vct / freq;
    //ts->tv_nsec = (vct % freq) * billion / freq;
    ts->tv_nsec = (vct - ((vct / freq) * freq)) * billion / freq;
}

static inline void
counter_to_timespec4(uint64_t vct, struct timespec *ts)
{
    struct counter *c = &counter_cntvct_el0;
    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct % c->freq) * billion / c->freq;
}

static inline int
counter_gettime1(volatile struct timespec *ts)
{
    uint64_t vct = get_cntvct();
    uint32_t freq = get_cntfrq();
    ts->tv_sec = vct / freq;
    ts->tv_nsec = (vct % freq) * billion / freq;

    return (0);
}

static inline int
counter_gettime2(struct timespec *ts)
{
    struct counter *c = &counter_cntvct_el0;
    uint64_t vct = get_cntvct();

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;

    return (0);
}

int counter_gettime3(struct timespec *ts);
int counter_gettime4(struct timespec *ts);

#ifdef __cplusplus
}
#endif

#endif /* COUNTER_COUNTER_TEST_H */
