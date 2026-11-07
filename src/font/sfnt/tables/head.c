#include "font/sfnt/tables/tables.h"

void table_head(const Font *f, const Stats *st, Buf *out)
{
	buf_u32(out, 0x00010000);       /* version */
	buf_u32(out, 0x00010000);       /* fontRevision 1.0 */
	buf_u32(out, 0);                /* checkSumAdjustment, patched later */
	buf_u32(out, 0x5F0F3CF5);       /* magic */
	buf_u16(out, 0x000B);           /* baseline y=0, lsb x=0, integer ppem */
	buf_u16(out, (uint16_t)f->info.upm);
	buf_i64(out, st->date);         /* created */
	buf_i64(out, st->date);         /* modified */
	buf_i16(out, (int16_t)st->all.xmin);
	buf_i16(out, (int16_t)st->all.ymin);
	buf_i16(out, (int16_t)st->all.xmax);
	buf_i16(out, (int16_t)st->all.ymax);
	buf_u16(out, 0);                /* macStyle */
	buf_u16(out, 8);                /* lowestRecPPEM */
	buf_i16(out, 2);                /* fontDirectionHint */
	buf_i16(out, 1);                /* indexToLocFormat: long */
	buf_i16(out, 0);                /* glyphDataFormat */
}
