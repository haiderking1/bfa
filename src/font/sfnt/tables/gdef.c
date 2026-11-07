#include "font/sfnt/tables/tables.h"
#include "font/sfnt/tables/otl.h"
#include "base/mem.h"

#include <stdlib.h>

void table_gdef(const Font *f, const Stats *st, Buf *out)
{
	(void)st;
	int *cls = xmalloc((size_t)f->gs.n * sizeof *cls);
	for (int i = 0; i < f->gs.n; i++)
		cls[i] = (int)f->gs.g[i].cls;
	buf_u16(out, 1);
	buf_u16(out, 0);
	buf_u16(out, 12);               /* glyphClassDef */
	buf_u16(out, 0);                /* attachList */
	buf_u16(out, 0);                /* ligCaretList */
	buf_u16(out, 0);                /* markAttachClassDef */
	otl_classdef(out, cls, f->gs.n);
	free(cls);
}
