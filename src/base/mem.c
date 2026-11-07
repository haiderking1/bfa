#include "base/mem.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void oom(size_t n)
{
	fprintf(stderr, "bfa: out of memory (%zu bytes)\n", n);
	abort();
}

void *xmalloc(size_t n)
{
	void *p = malloc(n ? n : 1);
	if (!p)
		oom(n);
	return p;
}

void *xcalloc(size_t count, size_t n)
{
	void *p = calloc(count ? count : 1, n ? n : 1);
	if (!p)
		oom(count * n);
	return p;
}

void *xrealloc(void *p, size_t n)
{
	void *q = realloc(p, n ? n : 1);
	if (!q)
		oom(n);
	return q;
}

char *xstrdup(const char *s)
{
	size_t n = strlen(s) + 1;
	char *d = xmalloc(n);
	memcpy(d, s, n);
	return d;
}

void xgrow(void **p, int *cap, int need, size_t sz)
{
	if (need <= *cap)
		return;
	int c = *cap ? *cap : 8;
	while (c < need)
		c *= 2;
	*p = xrealloc(*p, (size_t)c * sz);
	*cap = c;
}
