#include "font/sfnt/tables/tables.h"

#include <string.h>

typedef struct {
	uint32_t lo, hi;
	int bit;
} URange;

static const URange ranges[] = {
	{0x0000, 0x007F, 0},   /* basic latin */
	{0x0080, 0x00FF, 1},   /* latin-1 supplement */
	{0x0600, 0x06FF, 13},  /* arabic */
	{0x2000, 0x206F, 31},  /* general punctuation */
	{0xFB50, 0xFDFF, 63},  /* arabic presentation forms-a */
	{0xFE70, 0xFEFF, 67},  /* arabic presentation forms-b */
};

void table_os2(const Font *f, const Stats *st, Buf *out)
{
	const FontInfo *in = &f->info;
	uint32_t ur[4] = {0};
	uint32_t first = 0xFFFF, last = 0;
	for (int i = 0; i < st->ncmap; i++) {
		uint32_t cp = st->cmap[i].cp;
		if (cp < first) first = cp;
		if (cp > last) last = cp;
		for (size_t r = 0; r < sizeof ranges / sizeof *ranges; r++)
			if (cp >= ranges[r].lo && cp <= ranges[r].hi)
				ur[ranges[r].bit / 32] |= 1u << (ranges[r].bit % 32);
	}
	if (last > 0xFFFF)
		last = 0xFFFF;
	int upm = in->upm;

	buf_u16(out, 4);                        /* version */
	buf_i16(out, (int16_t)st->avg_width);
	buf_u16(out, 400);                      /* usWeightClass */
	buf_u16(out, 5);                        /* usWidthClass */
	buf_u16(out, 0);                        /* fsType: installable */
	buf_i16(out, (int16_t)(upm * 65 / 100)); /* subscript x size */
	buf_i16(out, (int16_t)(upm * 60 / 100)); /* subscript y size */
	buf_i16(out, 0);
	buf_i16(out, (int16_t)(upm * 75 / 1000));
	buf_i16(out, (int16_t)(upm * 65 / 100)); /* superscript */
	buf_i16(out, (int16_t)(upm * 60 / 100));
	buf_i16(out, 0);
	buf_i16(out, (int16_t)(upm * 35 / 100));
	buf_i16(out, (int16_t)in->stroke);      /* strikeout size */
	buf_i16(out, (int16_t)(in->x_height / 2 + in->stroke / 2));
	buf_i16(out, 0);                        /* sFamilyClass */
	buf_zero(out, 10);                      /* panose */
	for (int i = 0; i < 4; i++)
		buf_u32(out, ur[i]);
	char vend[4] = {' ', ' ', ' ', ' '};
	memcpy(vend, in->vendor, strnlen(in->vendor, 4));
	buf_bytes(out, vend, 4);
	buf_u16(out, 0x00C0);                   /* REGULAR | USE_TYPO_METRICS */
	buf_u16(out, (uint16_t)first);
	buf_u16(out, (uint16_t)last);
	buf_i16(out, (int16_t)in->ascender);
	buf_i16(out, (int16_t)in->descender);
	buf_i16(out, (int16_t)in->line_gap);
	buf_u16(out, (uint16_t)in->win_ascent);
	buf_u16(out, (uint16_t)in->win_descent);
	buf_u32(out, 1u << 6);                  /* code page 1256 arabic */
	buf_u32(out, 0);
	buf_i16(out, (int16_t)in->x_height);
	buf_i16(out, (int16_t)in->cap_height);
	buf_u16(out, 0);                        /* usDefaultChar */
	buf_u16(out, 0x20);                     /* usBreakChar */
	buf_u16(out, 4);                        /* usMaxContext */
}
