#include "font/sfnt/tables/tables.h"

#include <stdio.h>
#include <string.h>

typedef struct {
	int id;
	char text[128];
} NameRec;

void table_name(const Font *f, const Stats *st, Buf *out)
{
	(void)st;
	const FontInfo *in = &f->info;
	NameRec rec[7];
	int n = 0;
	char ps[64];
	size_t k = 0;
	for (const char *s = in->family; *s && k + 1 < sizeof ps; s++)
		if (*s != ' ')
			ps[k++] = *s;
	ps[k] = 0;

	rec[n].id = 0; snprintf(rec[n++].text, 128, "%s", in->copyright);
	rec[n].id = 1; snprintf(rec[n++].text, 128, "%s", in->family);
	rec[n].id = 2; snprintf(rec[n++].text, 128, "%s", in->style);
	rec[n].id = 3; snprintf(rec[n++].text, 128, "%s;%s;%s-%s", in->version, in->vendor, ps, in->style);
	rec[n].id = 4; snprintf(rec[n++].text, 128, "%s %s", in->family, in->style);
	rec[n].id = 5; snprintf(rec[n++].text, 128, "Version %s", in->version);
	rec[n].id = 6; snprintf(rec[n++].text, 128, "%s-%s", ps, in->style);

	Buf strs;
	buf_init(&strs);
	buf_u16(out, 0);                /* format */
	buf_u16(out, (uint16_t)n);
	buf_u16(out, (uint16_t)(6 + 12 * n));
	for (int i = 0; i < n; i++) {
		size_t len = strlen(rec[i].text);
		buf_u16(out, 3);        /* windows */
		buf_u16(out, 1);        /* unicode bmp */
		buf_u16(out, 0x0409);   /* en-US */
		buf_u16(out, (uint16_t)rec[i].id);
		buf_u16(out, (uint16_t)(len * 2));
		buf_u16(out, (uint16_t)strs.len);
		for (size_t c = 0; c < len; c++)
			buf_u16(&strs, (uint8_t)rec[i].text[c]);
	}
	buf_bytes(out, strs.data, strs.len);
	buf_free(&strs);
}
