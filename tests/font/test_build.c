#include "check.h"
#include "font/build/build.h"
#include "font/shape/joining.h"

#include <stdio.h>
#include <string.h>

static const FontInfo info = {
	.family = "Bfa Arabic", .style = "Regular", .version = "1.0",
	.copyright = "test", .vendor = "BFA", .upm = 1000,
	.ascender = 900, .descender = -500, .line_gap = 100,
	.x_height = 300, .cap_height = 720, .stroke = 74,
};

static int find_cp(const Font *f, uint32_t cp)
{
	for (int i = 0; i < f->gs.n; i++)
		for (int k = 0; k < f->gs.g[i].nuni; k++)
			if (f->gs.g[i].uni[k] == cp)
				return i;
	return -1;
}

int main(void)
{
	Font f;
	font_init(&f, &info);
	build_font(&f);

	CHECK(!strcmp(f.gs.g[0].name, ".notdef"));
	for (int i = 0; i < f.gs.n; i++) {
		const Glyph *g = &f.gs.g[i];
		bool blank = !strcmp(g->name, "space") || !strcmp(g->name, "nbspace") ||
			     !strcmp(g->name, "zwj") || !strcmp(g->name, "zwnj");
		if (!blank && g->cls != GC_MARK)
			CHECK(g->ol.n > 0);
		if (g->cls != GC_MARK && strcmp(g->name, "zwj") && strcmp(g->name, "zwnj"))
			CHECK(g->adv > 0);
		for (int c = 0; c < g->ol.n; c++)
			CHECK(g->ol.c[c].n >= 3);
		Box b;
		if (outline_box(&g->ol, &b)) {
			CHECK(b.ymax <= f.info.win_ascent);
			CHECK(-b.ymin <= f.info.win_descent);
		}
	}

	/* every letter and presentation form reaches a glyph */
	int n;
	const ArabicLetter *al = arabic_letters(&n);
	for (int i = 0; i < n; i++) {
		CHECK(find_cp(&f, al[i].cp) >= 0);
		for (int k = 0; k < FORM_COUNT; k++)
			if (al[i].pres[k])
				CHECK(find_cp(&f, al[i].pres[k]) >= 0);
	}
	int nl;
	const LamAlef *la = lam_alefs(&nl);
	for (int i = 0; i < nl; i++) {
		CHECK(find_cp(&f, la[i].isol) >= 0);
		CHECK(find_cp(&f, la[i].fina) >= 0);
	}

	/* joining glyphs leave no gap: the baseline crosses both edges */
	int tw = glyphset_find(&f.gs, "tatweel");
	CHECK(tw >= 0);
	if (tw >= 0) {
		Box b;
		outline_box(&f.gs.g[tw].ol, &b);
		CHECK(b.xmin < 0);
		CHECK(b.xmax > f.gs.g[tw].adv);
		CHECK_EQ(b.ymin, 0);
		CHECK_EQ(b.ymax, 74);
	}

	SingleFeature *init = font_single(&f, "init");
	CHECK(init->n > 20);
	LigFeature *rlig = font_lig(&f, "rlig", 1);
	CHECK_EQ(rlig->n, 8);

	font_free(&f);
	return CHECK_DONE();
}
