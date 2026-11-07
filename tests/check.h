#ifndef BFA_TESTS_CHECK_H
#define BFA_TESTS_CHECK_H

#include <stdio.h>

static int check_failures;

#define CHECK(cond)                                                            \
	do {                                                                   \
		if (!(cond)) {                                                 \
			fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, \
				__LINE__, #cond);                              \
			check_failures++;                                      \
		}                                                              \
	} while (0)

#define CHECK_EQ(a, b)                                                         \
	do {                                                                   \
		long long a_ = (long long)(a), b_ = (long long)(b);            \
		if (a_ != b_) {                                                \
			fprintf(stderr, "%s:%d: %s == %s: %lld != %lld\n",     \
				__FILE__, __LINE__, #a, #b, a_, b_);           \
			check_failures++;                                      \
		}                                                              \
	} while (0)

#define CHECK_DONE() (check_failures ? 1 : 0)

#endif
