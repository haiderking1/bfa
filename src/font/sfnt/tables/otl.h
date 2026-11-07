#ifndef BFA_FONT_SFNT_TABLES_OTL_H
#define BFA_FONT_SFNT_TABLES_OTL_H

#include "base/buf.h"

/* shared opentype layout pieces */
void otl_coverage(Buf *out, const int *gids, int n); /* gids sorted, unique */
void otl_classdef(Buf *out, const int *cls, int nglyphs);

/* a list of sub-blobs addressed by 16-bit offsets from one base */
typedef struct {
	Buf *item;
	int n, cap;
} Blobs;

Buf *blobs_add(Blobs *b);
void blobs_free(Blobs *b);
size_t blobs_size(const Blobs *b);

/* ScriptList for DFLT and arab, each listing every feature index */
void otl_scripts(Buf *out, int nfeatures);

#endif
