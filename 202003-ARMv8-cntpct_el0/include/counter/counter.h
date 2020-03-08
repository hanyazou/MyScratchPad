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

int counter_init(void);
void counter_show_params(void);

uint32_t counter_freq;

static inline void
counter_to_timespec(uint64_t vct, struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    ts->tv_sec = vct / counter_freq;
    ts->tv_nsec = (vct % counter_freq) * billion / counter_freq;
}

void counter_to_timespec1(uint64_t vct, struct timespec *ts);
void counter_to_timespec2(uint64_t vct, struct timespec *ts);
void counter_to_timespec3(uint64_t vct, struct timespec *ts);

static inline void
counter_to_timespec4(uint64_t vct, struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    uint32_t freq = get_cntfrq();
    ts->tv_sec = vct / freq;
    ts->tv_nsec = (vct % freq) * billion / freq;
}

static inline void
counter_gettime(volatile struct timespec *ts)
{
    uint64_t billion = (1000000000LL);  /* 1,000,000,000 < 1^32 = 4,294,967,296 */
    uint64_t vct = get_cntvct();
    uint32_t freq = get_cntfrq();
    ts->tv_sec = vct / freq;
    ts->tv_nsec = (vct % freq) * billion / freq;
}

void counter_gettime1(struct timespec *ts);
void counter_gettime2(struct timespec *ts);
