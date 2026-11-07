#ifndef BFA_BASE_MEM_H
#define BFA_BASE_MEM_H

#include <stddef.h>

void *xmalloc(size_t n);
void *xcalloc(size_t count, size_t n);
void *xrealloc(void *p, size_t n);
char *xstrdup(const char *s);

/* grow *p (holding *cap items of size sz) so it can hold at least need items */
void xgrow(void **p, int *cap, int need, size_t sz);

#define XGROW(arr, cap, need) xgrow((void **)&(arr), &(cap), (need), sizeof *(arr))

#endif
