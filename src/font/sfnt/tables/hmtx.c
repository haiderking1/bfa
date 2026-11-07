#include "font/sfnt/tables/tables.h"

void table_hmtx(const Font *f, const Stats *st, Buf *out)
{
	for (int i = 0; i < f->gs.n; i++) {
		buf_u16(out, (uint16_t)f->gs.g[i].adv);
		buf_i16(out, (int16_t)st->box[i].xmin);
	}
}
