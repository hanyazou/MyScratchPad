#include <counter/counter.h>
#include <stdio.h>
#include <counter_priv.h>

struct counter counter_cntvct_el0 = { 0 };

int
counter_init(void)
{
    struct counter *c = &counter_cntvct_el0;

    /* get clock frequency */
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

int
counter_gettime(struct timespec *ts)
{
    struct counter *c = &counter_cntvct_el0;
    uint64_t vct = get_cntvct();

    ts->tv_sec = vct / c->freq;
    ts->tv_nsec = (vct - ((vct / c->freq) * c->freq)) * billion / c->freq;

    return (0);
}
