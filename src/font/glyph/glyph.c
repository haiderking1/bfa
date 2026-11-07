#include "font/glyph/glyph.h"
#include "base/mem.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void glyphset_free(GlyphSet *gs)
{
	for (int i = 0; i < gs->n; i++) {
		free(gs->g[i].name);
		outline_free(&gs->g[i].ol);
	}
	free(gs->g);
	gs->g = NULL;
	gs->n = gs->cap = 0;
}

int glyphset_add(GlyphSet *gs, const char *name)
{
	if (glyphset_find(gs, name) >= 0) {
		fprintf(stderr, "bfa: duplicate glyph %s\n", name);
		abort();
	}
	XGROW(gs->g, gs->cap, gs->n + 1);
	Glyph *g = &gs->g[gs->n];
	memset(g, 0, sizeof *g);
	g->name = xstrdup(name);
	outline_init(&g->ol);
	return gs->n++;
}

int glyphset_find(const GlyphSet *gs, const char *name)
{
	for (int i = 0; i < gs->n; i++)
		if (!strcmp(gs->g[i].name, name))
			return i;
	return -1;
}

void glyph_map(Glyph *g, uint32_t cp)
{
	if (g->nuni >= GLYPH_MAX_UNI) {
		fprintf(stderr, "bfa: too many codepoints on %s\n", g->name);
		abort();
	}
	g->uni[g->nuni++] = cp;
}
