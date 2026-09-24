/* solution_mle.c — allocates a 1 GB boolean sieve regardless of N.
   With memory limit 256 MB: malloc() returns NULL (RLIMIT_AS exceeded),
   then the NULL dereference triggers SIGSEGV → process killed → grader
   reports RTE (which is MLE in disguise).
   Passes subtask 1 (small N, small values) if memory limit is not enforced,
   but always triggers MLE when the 256 MB limit is active. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIEVE_SIZE 1000000000  /* 1 GB */

int main(void) {
    int n;
    scanf("%d", &n);
    int* a = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);

    /* Wasteful: allocate 1 GB regardless of actual value range. */
    unsigned char* seen = malloc(SIEVE_SIZE);
    memset(seen, 0, SIEVE_SIZE);   /* touches every page → SIGSEGV if MLE */

    int k = 0;
    for (int i = 0; i < n; i++) {
        int v = a[i] - 1;          /* map [1, 1e9] -> [0, 1e9-1] */
        if (!seen[v]) { seen[v] = 1; k++; }
    }

    printf("%d\n", k);
    free(seen);
    free(a);
    return 0;
}
