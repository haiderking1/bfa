#include "font/sfnt/tables/tables.h"
#include "base/mem.h"

#include <stdlib.h>

typedef struct {
	uint16_t start, end;
	int16_t delta;
} Seg;

/* format 4: runs of codepoints whose glyph ids step along with them */
static void format4(const Stats *st, Buf *out)
{
	Seg *seg = xmalloc((size_t)(st->ncmap + 1) * sizeof *seg);
	int ns = 0;
	for (int i = 0; i < st->ncmap; i++) {
		uint32_t cp = st->cmap[i].cp;
		if (cp > 0xFFFE)
			break;
		int gid = st->cmap[i].gid;
		if (ns && seg[ns - 1].end + 1 == cp &&
		    (uint16_t)(seg[ns - 1].delta + cp) == gid) {
			seg[ns - 1].end = (uint16_t)cp;
			continue;
		}
		seg[ns++] = (Seg){(uint16_t)cp, (uint16_t)cp, (int16_t)(gid - (int)cp)};
	}
	seg[ns++] = (Seg){0xFFFF, 0xFFFF, 1};

	int pow2 = 1, log2 = 0;
	while (pow2 * 2 <= ns) {
		pow2 *= 2;
		log2++;
	}
	buf_u16(out, 4);
	buf_u16(out, (uint16_t)(16 + 8 * ns));  /* length */
	buf_u16(out, 0);                        /* language */
	buf_u16(out, (uint16_t)(ns * 2));
	buf_u16(out, (uint16_t)(pow2 * 2));     /* searchRange */
	buf_u16(out, (uint16_t)log2);           /* entrySelector */
	buf_u16(out, (uint16_t)(ns * 2 - pow2 * 2));
	for (int i = 0; i < ns; i++)
		buf_u16(out, seg[i].end);
	buf_u16(out, 0);                        /* reservedPad */
	for (int i = 0; i < ns; i++)
		buf_u16(out, seg[i].start);
	for (int i = 0; i < ns; i++)
		buf_i16(out, seg[i].delta);
	for (int i = 0; i < ns; i++)
		buf_u16(out, 0);                /* idRangeOffset */
	free(seg);
}

void table_cmap(const Font *f, const Stats *st, Buf *out)
{
	(void)f;
	buf_u16(out, 0);                /* version */
	buf_u16(out, 2);                /* numTables */
	buf_u16(out, 0);                /* unicode */
	buf_u16(out, 3);                /* bmp */
	buf_u32(out, 20);
	buf_u16(out, 3);                /* windows */
	buf_u16(out, 1);                /* unicode bmp */
	buf_u32(out, 20);
	format4(st, out);
}
