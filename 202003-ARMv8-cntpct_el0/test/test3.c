#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <semaphore.h>
#include <sched.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <errno.h>
#include <math.h>

#include <counter/counter.h>

#define MAX_THREADS 4

struct context {
    pthread_t thread_id;
    int core_id;
    pthread_cond_t *cond;
    pthread_mutex_t *mutex;
    sem_t *sem;
    int *alive;
    struct timespec mc;
    struct timespec cc;
    int average;
    int errors;
};

int
setcpu(int cpu)
{
    cpu_set_t cpuset;

    int res;

    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    if (sched_setaffinity(0, sizeof(cpuset), &cpuset) != 0) {
        fprintf(stderr, "Error: sched_setaffinity() failed. (errno=%d)\n", errno);
        return -1;
    }

    return 0;
}

void*
worker(void *arg)
{
    struct context *ctx = arg;
    int cpu;
    pthread_t this_thread = pthread_self();
    struct sched_param params;
    struct timespec realtime;
 
    cpu = sched_getcpu();
    if (setcpu(ctx->core_id) != 0) {
        ctx->errors++;
    }
    printf("%d: Start on %d -> %d\n", ctx->core_id, cpu, sched_getcpu());
    if (ctx->core_id != sched_getcpu()) {
        fprintf(stderr, "Error: ctx->core_id != sched_getcpu()\n");
        ctx->errors++;
    }

    params.sched_priority = sched_get_priority_max(SCHED_FIFO);
    if (pthread_setschedparam(this_thread, SCHED_FIFO, &params) != 0) {
        fprintf(stderr, "Error: pthread_setschedparam() failed. (errno=%d)\n", errno);
        ctx->errors++;
    }

    do {
        pthread_mutex_lock(ctx->mutex);
        clock_gettime(CLOCK_REALTIME, &realtime);
        realtime.tv_sec += 3;
        sem_post(ctx->sem);
        if (pthread_cond_timedwait(ctx->cond, ctx->mutex, &realtime) != 0) {
            fprintf(stderr, "Error: pthread_cond_timedwait() failed. (errno=%d)\n", errno);
            ctx->errors++;
        }
        counter_gettime(&ctx->cc);
        clock_gettime(CLOCK_MONOTONIC, &ctx->mc);
        pthread_mutex_unlock(ctx->mutex);
    } while (*ctx->alive);
}

int
main(int ac, char *av[])
{
    int i, j;
    static struct context contexts[MAX_THREADS];
    pthread_mutex_t mutex[MAX_THREADS];
    pthread_cond_t cond;
    sem_t sem;
    int alive;
    int errors = 0;

    counter_init();
    pthread_cond_init(&cond, NULL);
    sem_init(&sem, 0, 0);
    alive = 1;
    if (setcpu(0) != 0) {
        errors++;
    }

    for (i = 0; i < MAX_THREADS; i++) {
        /*
         * You don't hove to lock any resource. But pthread_cond_wait() requires no null 
         * arg. So just create dummy mutex locks here for each thread so that they can run 
         * without waiting for lock.
         */
        pthread_mutex_init(&mutex[i], NULL);
        memset(&contexts[i], 0, sizeof(contexts[i]));
        contexts[i].core_id = i;
        contexts[i].mutex = &mutex[i];
        contexts[i].cond = &cond;
        contexts[i].sem = &sem;
        contexts[i].alive = &alive;
        if(pthread_create(&contexts[i].thread_id, NULL, worker, &contexts[i]) < 0) {
            fprintf(stderr, "Error: pthread_create() failed. (errno=%d)\n", errno);
            exit(1);
        }
    }

    for (i = 0; i < MAX_THREADS; i++) {
        sem_wait(&sem);
    }
    sleep(1); /* wait for one more second */

    for (j = 0; j < 50000; j++) {
        uint64_t base_mc;
        uint64_t base_cc;

        usleep(10000); /* wait for 10u seconds */
        pthread_cond_broadcast(&cond);

        for (i = 0; i < MAX_THREADS; i++) {
            sem_wait(&sem);
        }

        base_mc = 0;
        base_cc = 0;
        for (i = 0; i < MAX_THREADS; i++) {
            base_mc += (contexts[i].mc.tv_sec * 1000000000LL + contexts[i].mc.tv_nsec);
            base_cc += (contexts[i].cc.tv_sec * 1000000000LL + contexts[i].cc.tv_nsec);
        }
        base_mc /= MAX_THREADS;
        base_cc /= MAX_THREADS;

        for (i = 0; i < MAX_THREADS; i++) {
            uint64_t mc = contexts[i].mc.tv_sec * 1000000000LL + contexts[i].mc.tv_nsec;
            uint64_t cc = contexts[i].cc.tv_sec * 1000000000LL + contexts[i].cc.tv_nsec;
            if ((j % 100) == 0) {
                printf("%5d: %d: %d.%09d %+8d\n", j, contexts[i].core_id,
                       (int)contexts[i].mc.tv_sec, (int)contexts[i].mc.tv_nsec,
                       (int)(mc - base_mc));
                printf("          %d.%09d %+8d\n",
                       (int)contexts[i].cc.tv_sec, (int)contexts[i].cc.tv_nsec,
                       (int)(cc - base_cc));
            }
            contexts[i].average += (int)(cc - base_cc);
        }
    }

    for (i = 0; i < MAX_THREADS; i++) {
        printf("%d: %+8d\n", contexts[i].core_id, contexts[i].average / j);
        if (10000 < abs(contexts[i].average / j)) {
            printf("Error: 10000 < %8d\n", abs(contexts[i].average / j));
            errors++;
        }
    }

    alive = 0;
    pthread_cond_broadcast(&cond);
    for (i = 0; i < MAX_THREADS; i++) {
        pthread_join(contexts[i].thread_id, NULL);
        errors += contexts[i].errors;
    }

    if (errors != 0) {
        fprintf(stderr, "Error: error count = %d\n", errors);
    }
}
