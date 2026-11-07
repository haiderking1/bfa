#ifndef BFA_FONT_GLYPH_GLYPH_H
#define BFA_FONT_GLYPH_GLYPH_H

#include "font/outline/outline.h"

#include <stdint.h>

/* GDEF glyph classes */
typedef enum {
	GC_NONE = 0,
	GC_BASE = 1,
	GC_LIGATURE = 2,
	GC_MARK = 3,
} GlyphClass;

#define GLYPH_MAX_UNI 4

typedef struct {
	char *name;
	uint32_t uni[GLYPH_MAX_UNI];
	int nuni;
	int adv;
	GlyphClass cls;
	Outline ol;
} Glyph;

typedef struct {
	Glyph *g;
	int n, cap;
} GlyphSet;

void glyphset_free(GlyphSet *gs);
/* returns the new glyph's id */
int glyphset_add(GlyphSet *gs, const char *name);
int glyphset_find(const GlyphSet *gs, const char *name);
void glyph_map(Glyph *g, uint32_t cp);

#endif
