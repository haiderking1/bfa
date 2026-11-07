#include "font/sfnt/tables/tables.h"

#include <stdlib.h>

enum {
	ON_CURVE = 0x01,
	X_SHORT = 0x02,
	Y_SHORT = 0x04,
	REPEAT = 0x08,
	X_SAME_POS = 0x10,
	Y_SAME_POS = 0x20,
};

static uint8_t coord_flag(int d, uint8_t shortf, uint8_t samef)
{
	if (d == 0)
		return samef;
	if (d > -256 && d < 256)
		return (uint8_t)(shortf | (d > 0 ? samef : 0));
	return 0;
}

static void put_coords(Buf *out, const Outline *o, int axis, uint8_t shortf,
		       uint8_t samef)
{
	int prev = 0;
	for (int c = 0; c < o->n; c++)
		for (int k = 0; k < o->c[c].n; k++) {
			int v = axis ? o->c[c].p[k].y : o->c[c].p[k].x;
			int d = v - prev;
			prev = v;
			uint8_t fl = coord_flag(d, shortf, samef);
			if (fl & shortf)
				buf_u8(out, (uint8_t)abs(d));
			else if (!(fl & samef))
				buf_i16(out, (int16_t)d);
		}
}

static void simple_glyph(const Outline *o, const Box *b, Buf *out)
{
	buf_i16(out, (int16_t)o->n);
	buf_i16(out, (int16_t)b->xmin);
	buf_i16(out, (int16_t)b->ymin);
	buf_i16(out, (int16_t)b->xmax);
	buf_i16(out, (int16_t)b->ymax);
	int end = -1;
	for (int c = 0; c < o->n; c++) {
		end += o->c[c].n;
		buf_u16(out, (uint16_t)end);
	}
	buf_u16(out, 0);                /* no instructions */

	/* flags, run-length packed */
	int px = 0, py = 0, run = 0;
	uint8_t last = 0;
	for (int c = 0; c < o->n; c++)
		for (int k = 0; k < o->c[c].n; k++) {
			OPt p = o->c[c].p[k];
			uint8_t fl = (uint8_t)((p.on ? ON_CURVE : 0) |
					       coord_flag(p.x - px, X_SHORT, X_SAME_POS) |
					       coord_flag(p.y - py, Y_SHORT, Y_SAME_POS));
			px = p.x;
			py = p.y;
			if (run && fl == last && run < 256) {
				run++;
				continue;
			}
			if (run == 1) {
				buf_u8(out, last);
			} else if (run > 1) {
				buf_u8(out, last | REPEAT);
				buf_u8(out, (uint8_t)(run - 1));
			}
			last = fl;
			run = 1;
		}
	if (run == 1) {
		buf_u8(out, last);
	} else if (run > 1) {
		buf_u8(out, last | REPEAT);
		buf_u8(out, (uint8_t)(run - 1));
	}
	put_coords(out, o, 0, X_SHORT, X_SAME_POS);
	put_coords(out, o, 1, Y_SHORT, Y_SAME_POS);
}

void table_glyf(const Font *f, const Stats *st, Buf *glyf, Buf *loca)
{
	for (int i = 0; i < f->gs.n; i++) {
		buf_u32(loca, (uint32_t)glyf->len);
		const Glyph *g = &f->gs.g[i];
		if (g->ol.n)
			simple_glyph(&g->ol, &st->box[i], glyf);
		buf_pad4(glyf);
	}
	buf_u32(loca, (uint32_t)glyf->len);
}
