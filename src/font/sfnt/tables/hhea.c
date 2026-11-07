#include "font/sfnt/tables/tables.h"

void table_hhea(const Font *f, const Stats *st, Buf *out)
{
	buf_u32(out, 0x00010000);
	buf_i16(out, (int16_t)f->info.ascender);
	buf_i16(out, (int16_t)f->info.descender);
	buf_i16(out, (int16_t)f->info.line_gap);
	buf_u16(out, (uint16_t)st->adv_max);
	buf_i16(out, (int16_t)st->min_lsb);
	buf_i16(out, (int16_t)st->min_rsb);
	buf_i16(out, (int16_t)st->max_extent);
	buf_i16(out, 1);                /* caretSlopeRise */
	buf_i16(out, 0);                /* caretSlopeRun */
	buf_i16(out, 0);                /* caretOffset */
	buf_zero(out, 8);               /* reserved */
	buf_i16(out, 0);                /* metricDataFormat */
	buf_u16(out, (uint16_t)f->gs.n);
}
