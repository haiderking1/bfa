#ifndef BFA_TESTS_SFNT_READ_H
#define BFA_TESTS_SFNT_READ_H

#include "base/buf.h"

#include <string.h>

/* just enough of an sfnt reader to check what the writer produced */

typedef struct {
	const uint8_t *p;
	uint32_t len;
} Table;

static inline int sfnt_ntables(const uint8_t *f)
{
	return rd_u16(f + 4);
}

static inline Table sfnt_table(const uint8_t *f, const char *tag)
{
	int n = sfnt_ntables(f);
	for (int i = 0; i < n; i++) {
		const uint8_t *r = f + 12 + 16 * i;
		if (!memcmp(r, tag, 4))
			return (Table){f + rd_u32(r + 8), rd_u32(r + 12)};
	}
	return (Table){NULL, 0};
}

/* format 4 lookup over the first cmap subtable */
static inline int cmap_lookup(Table cmap, uint32_t cp)
{
	const uint8_t *sub = cmap.p + rd_u32(cmap.p + 8);
	if (rd_u16(sub) != 4)
		return -1;
	int segx2 = rd_u16(sub + 6);
	const uint8_t *ends = sub + 14, *starts = ends + segx2 + 2;
	const uint8_t *deltas = starts + segx2, *ranges = deltas + segx2;
	for (int i = 0; i < segx2 / 2; i++) {
		uint16_t end = rd_u16(ends + 2 * i), start = rd_u16(starts + 2 * i);
		if (cp > end)
			continue;
		if (cp < start || rd_u16(ranges + 2 * i))
			return 0;
		return (uint16_t)(cp + rd_u16(deltas + 2 * i));
	}
	return 0;
}

#endif
