#ifndef COUNTER_COUNTER_H
#define COUNTER_COUNTER_H

#ifdef __cplusplus
extern "C" {
#endif

struct timespec *ts;

int counter_init(void);
void counter_show_params(void);
int counter_gettime(struct timespec *ts);

#ifdef __cplusplus
}
#endif

#endif /* COUNTER_COUNTER_H */
