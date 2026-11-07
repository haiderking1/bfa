#include "font/sfnt/writer.h"
#include "font/sfnt/stats.h"
#include "font/sfnt/tables/tables.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
	char tag[4];
	Buf data;
} Table;

uint32_t sfnt_checksum(const uint8_t *p, size_t n)
{
	uint32_t sum = 0;
	for (size_t i = 0; i < n; i += 4) {
		uint8_t w[4] = {0, 0, 0, 0};
		memcpy(w, p + i, n - i < 4 ? n - i : 4);
		sum += rd_u32(w);
	}
	return sum;
}

static int tag_cmp(const void *a, const void *b)
{
	return memcmp(((const Table *)a)->tag, ((const Table *)b)->tag, 4);
}

typedef void (*TableFn)(const Font *, const Stats *, Buf *);

void sfnt_build(const Font *f, Buf *out)
{
	Stats st;
	stats_build(f, &st);

	enum { MAX_TABLES = 16 };
	Table t[MAX_TABLES];
	int nt = 0;
	static const struct {
		const char *tag;
		TableFn fn;
	} simple[] = {
		{"GDEF", table_gdef}, {"GSUB", table_gsub}, {"OS/2", table_os2},
		{"cmap", table_cmap}, {"head", table_head}, {"hhea", table_hhea},
		{"hmtx", table_hmtx}, {"maxp", table_maxp}, {"name", table_name},
		{"post", table_post},
	};
	for (size_t i = 0; i < sizeof simple / sizeof *simple; i++) {
		memcpy(t[nt].tag, simple[i].tag, 4);
		buf_init(&t[nt].data);
		simple[i].fn(f, &st, &t[nt].data);
		nt++;
	}
	if (font_has_marks(f)) {
		memcpy(t[nt].tag, "GPOS", 4);
		buf_init(&t[nt].data);
		table_gpos(f, &st, &t[nt].data);
		nt++;
	}
	memcpy(t[nt].tag, "glyf", 4);
	memcpy(t[nt + 1].tag, "loca", 4);
	buf_init(&t[nt].data);
	buf_init(&t[nt + 1].data);
	table_glyf(f, &st, &t[nt].data, &t[nt + 1].data);
	nt += 2;
	qsort(t, (size_t)nt, sizeof *t, tag_cmp);

	int pow2 = 1, log2 = 0;
	while (pow2 * 2 <= nt) {
		pow2 *= 2;
		log2++;
	}
	buf_u32(out, 0x00010000);
	buf_u16(out, (uint16_t)nt);
	buf_u16(out, (uint16_t)(pow2 * 16));
	buf_u16(out, (uint16_t)log2);
	buf_u16(out, (uint16_t)(nt * 16 - pow2 * 16));
	size_t off = 12 + 16 * (size_t)nt, head_at = 0;
	for (int i = 0; i < nt; i++) {
		buf_bytes(out, t[i].tag, 4);
		buf_u32(out, sfnt_checksum(t[i].data.data, t[i].data.len));
		buf_u32(out, (uint32_t)off);
		buf_u32(out, (uint32_t)t[i].data.len);
		if (!memcmp(t[i].tag, "head", 4))
			head_at = off;
		off += (t[i].data.len + 3) & ~(size_t)3;
	}
	for (int i = 0; i < nt; i++) {
		buf_bytes(out, t[i].data.data, t[i].data.len);
		buf_pad4(out);
		buf_free(&t[i].data);
	}
	uint32_t adj = 0xB1B0AFBAu - sfnt_checksum(out->data, out->len);
	buf_set_u32(out, head_at + HEAD_CHECKSUM_ADJ_OFFSET, adj);
	stats_free(&st);
}

int sfnt_save(const Font *f, const char *path)
{
	Buf b;
	buf_init(&b);
	sfnt_build(f, &b);
	int rc = -1;
	FILE *fp = fopen(path, "wb");
	if (fp) {
		rc = fwrite(b.data, 1, b.len, fp) == b.len ? 0 : -1;
		if (fclose(fp))
			rc = -1;
	}
	buf_free(&b);
	return rc;
}
