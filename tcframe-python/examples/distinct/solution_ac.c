/* solution_ac.c — O(N log N): sort then count adjacent distinct values. */
#include <stdio.h>
#include <stdlib.h>

static int cmp_int(const void* a, const void* b) {
    int x = *(const int*)a, y = *(const int*)b;
    return (x > y) - (x < y);
}

int main(void) {
    int n;
    scanf("%d", &n);
    int* a = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);

    qsort(a, n, sizeof(int), cmp_int);

    int k = 1;
    for (int i = 1; i < n; i++)
        if (a[i] != a[i - 1]) k++;

    printf("%d\n", k);
    free(a);
    return 0;
}
