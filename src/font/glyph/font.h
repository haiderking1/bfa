#ifndef BFA_FONT_GLYPH_FONT_H
#define BFA_FONT_GLYPH_FONT_H

#include "font/glyph/glyph.h"

typedef struct {
	const char *family, *style, *version, *copyright, *vendor;
	int upm;
	int ascender, descender, line_gap; /* typo metrics */
	int win_ascent, win_descent;       /* clipping box */
	int x_height, cap_height;
	int stroke;                        /* for strikeout/underline */
} FontInfo;

typedef struct {
	int from, to;
} SubstPair;

/* one single-substitution feature (isol, init, ...) */
typedef struct {
	char tag[5];
	SubstPair *p;
	int n, cap;
} SingleFeature;

#define LIG_MAX_COMP 4

typedef struct {
	int comp[LIG_MAX_COMP];
	int ncomp;
	int lig;
} LigRule;

typedef struct {
	char tag[5];
	LigRule *r;
	int n, cap;
	int ignore_marks;
} LigFeature;

#define FONT_MAX_FEATURES 8

typedef struct {
	FontInfo info;
	GlyphSet gs;
	SingleFeature single[FONT_MAX_FEATURES];
	int nsingle;
	LigFeature lig[FONT_MAX_FEATURES];
	int nlig;
} Font;

void font_init(Font *f, const FontInfo *info);
void font_free(Font *f);

SingleFeature *font_single(Font *f, const char *tag);
LigFeature *font_lig(Font *f, const char *tag, int ignore_marks);
void single_add(SingleFeature *sf, int from, int to);
void lig_add(LigFeature *lf, const int *comp, int ncomp, int lig);

#endif
