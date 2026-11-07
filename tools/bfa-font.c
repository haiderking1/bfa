#include "font/build/build.h"
#include "font/glyph/font.h"
#include "font/preview/sheet.h"
#include "font/sfnt/writer.h"

#include <stdio.h>
#include <string.h>

static const FontInfo info = {
	.family = "Bfa Arabic",
	.style = "Regular",
	.version = "1.000",
	.copyright = "Copyright 2026 the bfa authors",
	.vendor = "BFA",
	.upm = 1000,
	.ascender = 900,
	.descender = -500,
	.line_gap = 100,
	.x_height = 300,
	.cap_height = 720,
	.stroke = 84,
};

static int usage(void)
{
	fprintf(stderr, "usage: bfa-font -o font.ttf [-p sheet.png]\n");
	return 2;
}

int main(int argc, char **argv)
{
	const char *out = NULL, *sheet = NULL;
	for (int i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "-o") && i + 1 < argc)
			out = argv[++i];
		else if (!strcmp(argv[i], "-p") && i + 1 < argc)
			sheet = argv[++i];
		else
			return usage();
	}
	if (!out)
		return usage();
	Font f;
	font_init(&f, &info);
	build_font(&f);
	if (sfnt_save(&f, out)) {
		fprintf(stderr, "bfa-font: cannot write %s\n", out);
		font_free(&f);
		return 1;
	}
	if (sheet && sheet_write(&f, sheet, 16, 120)) {
		fprintf(stderr, "bfa-font: cannot write %s\n", sheet);
		font_free(&f);
		return 1;
	}
	printf("%s: %d glyphs\n", out, f.gs.n);
	font_free(&f);
	return 0;
}
