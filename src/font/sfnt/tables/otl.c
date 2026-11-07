#include "font/sfnt/tables/otl.h"
#include "base/mem.h"

#include <stdlib.h>

void otl_coverage(Buf *out, const int *gids, int n)
{
	buf_u16(out, 1);
	buf_u16(out, (uint16_t)n);
	for (int i = 0; i < n; i++)
		buf_u16(out, (uint16_t)gids[i]);
}

void otl_classdef(Buf *out, const int *cls, int nglyphs)
{
	size_t at = out->len;
	buf_u16(out, 2);
	buf_u16(out, 0);
	int nr = 0;
	for (int i = 0; i < nglyphs;) {
		int j = i;
		while (j + 1 < nglyphs && cls[j + 1] == cls[i])
			j++;
		if (cls[i]) {
			buf_u16(out, (uint16_t)i);
			buf_u16(out, (uint16_t)j);
			buf_u16(out, (uint16_t)cls[i]);
			nr++;
		}
		i = j + 1;
	}
	buf_set_u16(out, at + 2, (uint16_t)nr);
}

Buf *blobs_add(Blobs *b)
{
	XGROW(b->item, b->cap, b->n + 1);
	Buf *x = &b->item[b->n++];
	buf_init(x);
	return x;
}

void blobs_free(Blobs *b)
{
	for (int i = 0; i < b->n; i++)
		buf_free(&b->item[i]);
	free(b->item);
	b->item = NULL;
	b->n = b->cap = 0;
}

size_t blobs_size(const Blobs *b)
{
	size_t s = 0;
	for (int i = 0; i < b->n; i++)
		s += b->item[i].len;
	return s;
}

void otl_scripts(Buf *out, int nfeatures)
{
	static const char *tags[2] = {"DFLT", "arab"};
	/* script table: defaultLangSys offset 4, no langsys records, then
	   the langsys itself */
	size_t script_len = 4 + 6 + 2 * (size_t)nfeatures;
	buf_u16(out, 2);
	for (int s = 0; s < 2; s++) {
		buf_bytes(out, tags[s], 4);
		buf_u16(out, (uint16_t)(2 + 6 * 2 + s * script_len));
	}
	for (int s = 0; s < 2; s++) {
		buf_u16(out, 4);        /* defaultLangSys */
		buf_u16(out, 0);        /* langSysCount */
		buf_u16(out, 0);        /* lookupOrder */
		buf_u16(out, 0xFFFF);   /* no required feature */
		buf_u16(out, (uint16_t)nfeatures);
		for (int i = 0; i < nfeatures; i++)
			buf_u16(out, (uint16_t)i);
	}
}
