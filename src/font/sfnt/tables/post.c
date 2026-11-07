#include "font/sfnt/tables/tables.h"

#include <string.h>

/* version 2 keeps glyph names, which makes the font readable in tools */
void table_post(const Font *f, const Stats *st, Buf *out)
{
	(void)st;
	buf_u32(out, 0x00020000);
	buf_u32(out, 0);                /* italicAngle */
	buf_i16(out, (int16_t)(-f->info.stroke * 2));
	buf_i16(out, (int16_t)f->info.stroke);
	buf_u32(out, 0);                /* isFixedPitch */
	buf_zero(out, 16);              /* memory hints */
	buf_u16(out, (uint16_t)f->gs.n);
	int custom = 0;
	for (int i = 0; i < f->gs.n; i++) {
		if (!strcmp(f->gs.g[i].name, ".notdef"))
			buf_u16(out, 0);
		else
			buf_u16(out, (uint16_t)(258 + custom++));
	}
	for (int i = 0; i < f->gs.n; i++) {
		const char *nm = f->gs.g[i].name;
		if (!strcmp(nm, ".notdef"))
			continue;
		size_t len = strlen(nm);
		if (len > 63)
			len = 63;
		buf_u8(out, (uint8_t)len);
		buf_bytes(out, nm, len);
	}
}
