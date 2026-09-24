/* solution_tle.c — O(N²): for each element, scan ALL previous elements
   (no early break) to check if seen.
   Passes subtask 1 (N <= 1000) but TLEs on subtask 2 (N <= 200000). */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n;
    scanf("%d", &n);
    int* a = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);

    int k = 0;
    for (int i = 0; i < n; i++) {
        int first = 1;
        /* No break: always scans all j < i — guaranteed O(N^2) */
        for (int j = 0; j < i; j++) {
            if (a[j] == a[i]) first = 0;
        }
        if (first) k++;
    }

    printf("%d\n", k);
    free(a);
    return 0;
}
