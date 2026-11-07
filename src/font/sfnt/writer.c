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

void sfnt_build(const Font *f, Buf *out)
{
	Stats st;
	stats_build(f, &st);

	enum { NT = 12 };
	Table t[NT];
	static const char *tags[NT] = {"GDEF", "GSUB", "OS/2", "cmap", "glyf", "head",
				       "hhea", "hmtx", "loca", "maxp", "name", "post"};
	for (int i = 0; i < NT; i++) {
		memcpy(t[i].tag, tags[i], 4);
		buf_init(&t[i].data);
	}
	table_gdef(f, &st, &t[0].data);
	table_gsub(f, &st, &t[1].data);
	table_os2(f, &st, &t[2].data);
	table_cmap(f, &st, &t[3].data);
	table_glyf(f, &st, &t[4].data, &t[8].data);
	table_head(f, &st, &t[5].data);
	table_hhea(f, &st, &t[6].data);
	table_hmtx(f, &st, &t[7].data);
	table_maxp(f, &st, &t[9].data);
	table_name(f, &st, &t[10].data);
	table_post(f, &st, &t[11].data);
	qsort(t, NT, sizeof *t, tag_cmp);

	int pow2 = 1, log2 = 0;
	while (pow2 * 2 <= NT) {
		pow2 *= 2;
		log2++;
	}
	buf_u32(out, 0x00010000);
	buf_u16(out, NT);
	buf_u16(out, (uint16_t)(pow2 * 16));
	buf_u16(out, (uint16_t)log2);
	buf_u16(out, (uint16_t)(NT * 16 - pow2 * 16));
	size_t off = 12 + 16 * NT, head_at = 0;
	for (int i = 0; i < NT; i++) {
		buf_bytes(out, t[i].tag, 4);
		buf_u32(out, sfnt_checksum(t[i].data.data, t[i].data.len));
		buf_u32(out, (uint32_t)off);
		buf_u32(out, (uint32_t)t[i].data.len);
		if (!memcmp(t[i].tag, "head", 4))
			head_at = off;
		off += (t[i].data.len + 3) & ~(size_t)3;
	}
	for (int i = 0; i < NT; i++) {
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
