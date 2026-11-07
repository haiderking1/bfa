#include "check.h"
#include "sfnt_read.h"
#include "font/glyph/font.h"
#include "font/sfnt/writer.h"

static const FontInfo info = {
	.family = "Test Font", .style = "Regular", .version = "1.0",
	.copyright = "test", .vendor = "TEST", .upm = 1000,
	.ascender = 800, .descender = -200, .line_gap = 0,
	.win_ascent = 900, .win_descent = 300,
	.x_height = 500, .cap_height = 700, .stroke = 80,
};

static void square(Glyph *g, int x0, int y0, int x1, int y1)
{
	OContour *c = outline_add(&g->ol);
	contour_push(c, x0, y0, true);
	contour_push(c, x0, y1, true);
	contour_push(c, x1, y1, true);
	contour_push(c, x1, y0, true);
}

int main(void)
{
	Font f;
	font_init(&f, &info);
	int notdef = glyphset_add(&f.gs, ".notdef");
	f.gs.g[notdef].adv = 500;
	square(&f.gs.g[notdef], 50, 0, 450, 700);
	int a = glyphset_add(&f.gs, "a");
	f.gs.g[a].adv = 600;
	square(&f.gs.g[a], 100, 0, 500, 300);
	glyph_map(&f.gs.g[a], 0x0627);
	glyph_map(&f.gs.g[a], 0xFE8D);
	int b = glyphset_add(&f.gs, "b");
	f.gs.g[b].adv = 300;
	square(&f.gs.g[b], -10, -100, 310, 1000); /* big coords: long deltas */
	glyph_map(&f.gs.g[b], 0x0628);
	single_add(font_single(&f, "init"), a, b);
	int comp[2] = {a, b};
	lig_add(font_lig(&f, "rlig", 1), comp, 2, a);

	Buf out;
	buf_init(&out);
	sfnt_build(&f, &out);

	CHECK_EQ(rd_u32(out.data), 0x00010000);
	int n = sfnt_ntables(out.data);
	CHECK_EQ(n, 12);
	for (int i = 0; i + 1 < n; i++)
		CHECK(memcmp(out.data + 12 + 16 * i, out.data + 12 + 16 * (i + 1), 4) < 0);
	/* every table checksum matches, head counted with adjustment zeroed */
	for (int i = 0; i < n; i++) {
		const uint8_t *r = out.data + 12 + 16 * i;
		uint32_t off = rd_u32(r + 8), len = rd_u32(r + 12);
		CHECK_EQ(off % 4, 0);
		uint32_t sum = sfnt_checksum(out.data + off, len);
		if (!memcmp(r, "head", 4))
			sum -= rd_u32(out.data + off + 8);
		CHECK_EQ(sum, rd_u32(r + 4));
	}
	CHECK_EQ(sfnt_checksum(out.data, out.len), 0xB1B0AFBA);

	Table cmap = sfnt_table(out.data, "cmap");
	CHECK(cmap.p != NULL);
	CHECK_EQ(cmap_lookup(cmap, 0x0627), a);
	CHECK_EQ(cmap_lookup(cmap, 0xFE8D), a);
	CHECK_EQ(cmap_lookup(cmap, 0x0628), b);
	CHECK_EQ(cmap_lookup(cmap, 0x0629), 0);

	Table maxp = sfnt_table(out.data, "maxp");
	CHECK_EQ(rd_u16(maxp.p + 4), 3);

	Table head = sfnt_table(out.data, "head");
	CHECK_EQ(rd_u32(head.p + 12), 0x5F0F3CF5);
	CHECK_EQ((int16_t)rd_u16(head.p + 36), -10);   /* xMin */
	CHECK_EQ((int16_t)rd_u16(head.p + 42), 1000);  /* yMax */

	Table loca = sfnt_table(out.data, "loca"), glyf = sfnt_table(out.data, "glyf");
	CHECK_EQ(loca.len, 4 * 4);
	for (int i = 0; i < 3; i++)
		CHECK(rd_u32(loca.p + 4 * i) <= rd_u32(loca.p + 4 * (i + 1)));
	CHECK_EQ(rd_u32(loca.p + 12), glyf.len);
	/* glyph b: one contour, bbox as drawn */
	const uint8_t *gb = glyf.p + rd_u32(loca.p + 8);
	CHECK_EQ((int16_t)rd_u16(gb), 1);
	CHECK_EQ((int16_t)rd_u16(gb + 2), -10);
	CHECK_EQ((int16_t)rd_u16(gb + 4), -100);

	Table hmtx = sfnt_table(out.data, "hmtx");
	CHECK_EQ(rd_u16(hmtx.p + 4), 600);
	CHECK_EQ((int16_t)rd_u16(hmtx.p + 10), -10);

	Table gsub = sfnt_table(out.data, "GSUB");
	CHECK(gsub.p != NULL);
	const uint8_t *fl = gsub.p + rd_u16(gsub.p + 6);
	CHECK_EQ(rd_u16(fl), 2);
	CHECK(!memcmp(fl + 2, "init", 4));
	CHECK(!memcmp(fl + 8, "rlig", 4));

	buf_free(&out);
	font_free(&f);
	return CHECK_DONE();
}
