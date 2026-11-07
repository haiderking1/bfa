#ifndef BFA_FONT_SFNT_STATS_H
#define BFA_FONT_SFNT_STATS_H

#include "font/glyph/font.h"

#include <stdint.h>

typedef struct {
	uint32_t cp;
	int gid;
} CMapEntry;

/* numbers several tables need, computed once */
typedef struct {
	Box *box;        /* per glyph */
	Box all;         /* union of all glyph boxes */
	int max_points, max_contours;
	int adv_max, min_lsb, min_rsb, max_extent, avg_width;
	CMapEntry *cmap; /* sorted by codepoint */
	int ncmap;
	int64_t date;    /* seconds since 1904 */
} Stats;

void stats_build(const Font *f, Stats *st);
void stats_free(Stats *st);

#endif
