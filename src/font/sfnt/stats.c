#include "font/sfnt/stats.h"
#include "base/mem.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

/* fixed build date keeps the output byte-for-byte reproducible */
#define BUILD_DATE_UNIX 1794009600LL /* 2026-11-07 */
#define MAC_EPOCH_OFFSET 2082844800LL

static int cmap_cmp(const void *a, const void *b)
{
	uint32_t x = ((const CMapEntry *)a)->cp, y = ((const CMapEntry *)b)->cp;
	return x < y ? -1 : x > y;
}

void stats_build(const Font *f, Stats *st)
{
	const GlyphSet *gs = &f->gs;
	st->box = xcalloc((size_t)gs->n, sizeof *st->box);
	st->all = (Box){INT_MAX, INT_MAX, INT_MIN, INT_MIN};
	st->max_points = st->max_contours = 0;
	st->adv_max = 0;
	st->min_lsb = st->min_rsb = INT_MAX;
	st->max_extent = INT_MIN;
	long wsum = 0;
	int wn = 0;
	st->ncmap = 0;
	for (int i = 0; i < gs->n; i++) {
		const Glyph *g = &gs->g[i];
		st->ncmap += g->nuni;
		if (g->adv > st->adv_max)
			st->adv_max = g->adv;
		if (g->adv > 0) {
			wsum += g->adv;
			wn++;
		}
		Box *b = &st->box[i];
		if (!outline_box(&g->ol, b))
			continue;
		if (b->xmin < st->all.xmin) st->all.xmin = b->xmin;
		if (b->ymin < st->all.ymin) st->all.ymin = b->ymin;
		if (b->xmax > st->all.xmax) st->all.xmax = b->xmax;
		if (b->ymax > st->all.ymax) st->all.ymax = b->ymax;
		int pts = outline_points(&g->ol);
		if (pts > st->max_points) st->max_points = pts;
		if (g->ol.n > st->max_contours) st->max_contours = g->ol.n;
		if (b->xmin < st->min_lsb) st->min_lsb = b->xmin;
		if (g->adv - b->xmax < st->min_rsb) st->min_rsb = g->adv - b->xmax;
		if (b->xmax > st->max_extent) st->max_extent = b->xmax;
	}
	if (st->all.xmin > st->all.xmax)
		st->all = (Box){0, 0, 0, 0};
	if (st->min_lsb == INT_MAX) st->min_lsb = 0;
	if (st->min_rsb == INT_MAX) st->min_rsb = 0;
	if (st->max_extent == INT_MIN) st->max_extent = 0;
	st->avg_width = wn ? (int)(wsum / wn) : 0;

	st->cmap = xmalloc((size_t)(st->ncmap ? st->ncmap : 1) * sizeof *st->cmap);
	int k = 0;
	for (int i = 0; i < gs->n; i++)
		for (int u = 0; u < gs->g[i].nuni; u++)
			st->cmap[k++] = (CMapEntry){gs->g[i].uni[u], i};
	qsort(st->cmap, (size_t)st->ncmap, sizeof *st->cmap, cmap_cmp);
	for (int i = 1; i < st->ncmap; i++)
		if (st->cmap[i].cp == st->cmap[i - 1].cp) {
			fprintf(stderr, "bfa: U+%04X mapped twice\n", st->cmap[i].cp);
			abort();
		}
	st->date = BUILD_DATE_UNIX + MAC_EPOCH_OFFSET;
}

void stats_free(Stats *st)
{
	free(st->box);
	free(st->cmap);
	st->box = NULL;
	st->cmap = NULL;
}
