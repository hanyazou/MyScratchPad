#ifndef COUNTER_COUNTER_PRIV_H
#define COUNTER_COUNTER_PRIV_H

#include <stdint.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

#define billion (1000000000LL)  /* 1,000,000,000 < 1^32 = 4,294,967,296 */

struct counter {
    int initialized;
    uint32_t sdiv, smul;
    uint32_t nsdiv, nsmul;
    uint64_t mask;
    uint32_t freq;
};

extern struct counter counter_cntvct_el0;

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

#ifdef __cplusplus
}
#endif

#endif /* COUNTER_COUNTER_PRIV_H */
