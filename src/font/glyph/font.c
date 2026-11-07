#include "font/glyph/font.h"
#include "base/mem.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void font_init(Font *f, const FontInfo *info)
{
	memset(f, 0, sizeof *f);
	f->info = *info;
}

void font_free(Font *f)
{
	glyphset_free(&f->gs);
	for (int i = 0; i < f->nsingle; i++)
		free(f->single[i].p);
	for (int i = 0; i < f->nlig; i++)
		free(f->lig[i].r);
	f->nsingle = f->nlig = 0;
}

static void set_tag(char dst[5], const char *tag)
{
	memset(dst, ' ', 4);
	memcpy(dst, tag, strnlen(tag, 4));
	dst[4] = 0;
}

SingleFeature *font_single(Font *f, const char *tag)
{
	for (int i = 0; i < f->nsingle; i++)
		if (!strncmp(f->single[i].tag, tag, 4))
			return &f->single[i];
	if (f->nsingle == FONT_MAX_FEATURES) {
		fprintf(stderr, "bfa: too many features\n");
		abort();
	}
	SingleFeature *sf = &f->single[f->nsingle++];
	set_tag(sf->tag, tag);
	return sf;
}

LigFeature *font_lig(Font *f, const char *tag, int ignore_marks)
{
	for (int i = 0; i < f->nlig; i++)
		if (!strncmp(f->lig[i].tag, tag, 4))
			return &f->lig[i];
	if (f->nlig == FONT_MAX_FEATURES) {
		fprintf(stderr, "bfa: too many features\n");
		abort();
	}
	LigFeature *lf = &f->lig[f->nlig++];
	set_tag(lf->tag, tag);
	lf->ignore_marks = ignore_marks;
	return lf;
}

void single_add(SingleFeature *sf, int from, int to)
{
	XGROW(sf->p, sf->cap, sf->n + 1);
	sf->p[sf->n++] = (SubstPair){from, to};
}

void lig_add(LigFeature *lf, const int *comp, int ncomp, int lig)
{
	XGROW(lf->r, lf->cap, lf->n + 1);
	LigRule *r = &lf->r[lf->n++];
	memset(r, 0, sizeof *r);
	memcpy(r->comp, comp, (size_t)ncomp * sizeof *comp);
	r->ncomp = ncomp;
	r->lig = lig;
}
