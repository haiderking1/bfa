#include "font/sfnt/tables/tables.h"
#include "font/sfnt/tables/otl.h"
#include "base/mem.h"

#include <stdbool.h>
#include <stdlib.h>

enum { LOOKUP_MARK_BASE = 4, LOOKUP_MARK_MARK = 6, MARK_CLASSES = 2 };

static void anchor(Buf *out, Anchor a)
{
	buf_u16(out, 1);
	buf_i16(out, (int16_t)a.x);
	buf_i16(out, (int16_t)a.y);
}

/* MarkBasePos format 1: every mark against every anchored base */
static void mark_base(const Font *f, Buf *out)
{
	int *marks = xmalloc((size_t)f->gs.n * sizeof *marks);
	int *bases = xmalloc((size_t)f->gs.n * sizeof *bases);
	int nm = 0, nb = 0;
	for (int i = 0; i < f->gs.n; i++) {
		const Glyph *g = &f->gs.g[i];
		if (!g->anchored)
			continue;
		if (g->cls == GC_MARK)
			marks[nm++] = i;
		else
			bases[nb++] = i;
	}

	Buf marr, barr;
	buf_init(&marr);
	buf_init(&barr);
	buf_u16(&marr, (uint16_t)nm);
	for (int i = 0; i < nm; i++) {
		const Glyph *g = &f->gs.g[marks[i]];
		buf_u16(&marr, g->side == MARK_ABOVE ? 0 : 1);
		buf_u16(&marr, (uint16_t)(2 + 4 * nm + 6 * i));
	}
	for (int i = 0; i < nm; i++)
		anchor(&marr, f->gs.g[marks[i]].attach);

	buf_u16(&barr, (uint16_t)nb);
	size_t aoff = 2 + 2 * MARK_CLASSES * (size_t)nb;
	for (int i = 0; i < nb; i++)
		for (int c = 0; c < MARK_CLASSES; c++)
			buf_u16(&barr, (uint16_t)(aoff + 6 * (MARK_CLASSES * (size_t)i + c)));
	for (int i = 0; i < nb; i++) {
		const Glyph *g = &f->gs.g[bases[i]];
		anchor(&barr, g->top);
		anchor(&barr, g->bottom);
	}

	Buf mcov, bcov;
	buf_init(&mcov);
	buf_init(&bcov);
	otl_coverage(&mcov, marks, nm);
	otl_coverage(&bcov, bases, nb);

	size_t at = 12;
	buf_u16(out, 1);
	buf_u16(out, (uint16_t)at);
	buf_u16(out, (uint16_t)(at + mcov.len));
	buf_u16(out, MARK_CLASSES);
	buf_u16(out, (uint16_t)(at + mcov.len + bcov.len));
	buf_u16(out, (uint16_t)(at + mcov.len + bcov.len + marr.len));
	buf_bytes(out, mcov.data, mcov.len);
	buf_bytes(out, bcov.data, bcov.len);
	buf_bytes(out, marr.data, marr.len);
	buf_bytes(out, barr.data, barr.len);

	buf_free(&marr);
	buf_free(&barr);
	buf_free(&mcov);
	buf_free(&bcov);
	free(marks);
	free(bases);
}

/* MarkMarkPos format 1: a mark stacks on the mark before it when both sit
   on the same side */
static void mark_mark(const Font *f, Buf *out)
{
	int *marks = xmalloc((size_t)f->gs.n * sizeof *marks);
	int nm = 0;
	for (int i = 0; i < f->gs.n; i++)
		if (f->gs.g[i].cls == GC_MARK && f->gs.g[i].anchored)
			marks[nm++] = i;

	Buf m1, m2, cov;
	buf_init(&m1);
	buf_init(&m2);
	buf_init(&cov);
	buf_u16(&m1, (uint16_t)nm);
	for (int i = 0; i < nm; i++) {
		buf_u16(&m1, f->gs.g[marks[i]].side == MARK_ABOVE ? 0 : 1);
		buf_u16(&m1, (uint16_t)(2 + 4 * nm + 6 * i));
	}
	for (int i = 0; i < nm; i++)
		anchor(&m1, f->gs.g[marks[i]].attach);

	/* a mark only offers the anchor on its own side, the other is null */
	buf_u16(&m2, (uint16_t)nm);
	size_t aoff = 2 + 2 * MARK_CLASSES * (size_t)nm;
	for (int i = 0; i < nm; i++) {
		bool above = f->gs.g[marks[i]].side == MARK_ABOVE;
		buf_u16(&m2, above ? (uint16_t)(aoff + 6 * (size_t)i) : 0);
		buf_u16(&m2, above ? 0 : (uint16_t)(aoff + 6 * (size_t)i));
	}
	for (int i = 0; i < nm; i++) {
		const Glyph *g = &f->gs.g[marks[i]];
		anchor(&m2, g->side == MARK_ABOVE ? g->top : g->bottom);
	}
	otl_coverage(&cov, marks, nm);

	size_t at = 12;
	buf_u16(out, 1);
	buf_u16(out, (uint16_t)at);
	buf_u16(out, (uint16_t)at);     /* same coverage for both roles */
	buf_u16(out, MARK_CLASSES);
	buf_u16(out, (uint16_t)(at + cov.len));
	buf_u16(out, (uint16_t)(at + cov.len + m1.len));
	buf_bytes(out, cov.data, cov.len);
	buf_bytes(out, m1.data, m1.len);
	buf_bytes(out, m2.data, m2.len);
	buf_free(&m1);
	buf_free(&m2);
	buf_free(&cov);
	free(marks);
}

static void lookup(Buf *out, int type, const Buf *sub)
{
	buf_u16(out, (uint16_t)type);
	buf_u16(out, 0);
	buf_u16(out, 1);
	buf_u16(out, 8);
	buf_bytes(out, sub->data, sub->len);
}

void table_gpos(const Font *f, const Stats *st, Buf *out)
{
	(void)st;
	Buf scripts, feats, lookups, sub;
	buf_init(&scripts);
	buf_init(&feats);
	buf_init(&lookups);
	buf_init(&sub);
	otl_scripts(&scripts, 2);

	/* features sorted by tag: mark -> lookup 0, mkmk -> lookup 1 */
	buf_u16(&feats, 2);
	buf_bytes(&feats, "mark", 4);
	buf_u16(&feats, 14);
	buf_bytes(&feats, "mkmk", 4);
	buf_u16(&feats, 20);
	for (int i = 0; i < 2; i++) {
		buf_u16(&feats, 0);
		buf_u16(&feats, 1);
		buf_u16(&feats, (uint16_t)i);
	}

	Buf l0, l1;
	buf_init(&l0);
	buf_init(&l1);
	mark_base(f, &sub);
	lookup(&l0, LOOKUP_MARK_BASE, &sub);
	buf_free(&sub);
	buf_init(&sub);
	mark_mark(f, &sub);
	lookup(&l1, LOOKUP_MARK_MARK, &sub);
	buf_u16(&lookups, 2);
	buf_u16(&lookups, 6);
	buf_u16(&lookups, (uint16_t)(6 + l0.len));
	buf_bytes(&lookups, l0.data, l0.len);
	buf_bytes(&lookups, l1.data, l1.len);
	buf_free(&l0);
	buf_free(&l1);

	buf_u16(out, 1);
	buf_u16(out, 0);
	buf_u16(out, 10);
	buf_u16(out, (uint16_t)(10 + scripts.len));
	buf_u16(out, (uint16_t)(10 + scripts.len + feats.len));
	buf_bytes(out, scripts.data, scripts.len);
	buf_bytes(out, feats.data, feats.len);
	buf_bytes(out, lookups.data, lookups.len);
	buf_free(&scripts);
	buf_free(&feats);
	buf_free(&lookups);
	buf_free(&sub);
}

bool font_has_marks(const Font *f)
{
	for (int i = 0; i < f->gs.n; i++)
		if (f->gs.g[i].cls == GC_MARK && f->gs.g[i].anchored)
			return true;
	return false;
}
