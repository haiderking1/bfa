#include "font/sfnt/tables/tables.h"

void table_maxp(const Font *f, const Stats *st, Buf *out)
{
	buf_u32(out, 0x00010000);
	buf_u16(out, (uint16_t)f->gs.n);
	buf_u16(out, (uint16_t)st->max_points);
	buf_u16(out, (uint16_t)st->max_contours);
	buf_u16(out, 0);                /* maxCompositePoints */
	buf_u16(out, 0);                /* maxCompositeContours */
	buf_u16(out, 2);                /* maxZones */
	buf_u16(out, 0);                /* maxTwilightPoints */
	buf_u16(out, 0);                /* maxStorage */
	buf_u16(out, 0);                /* maxFunctionDefs */
	buf_u16(out, 0);                /* maxInstructionDefs */
	buf_u16(out, 0);                /* maxStackElements */
	buf_u16(out, 0);                /* maxSizeOfInstructions */
	buf_u16(out, 0);                /* maxComponentElements */
	buf_u16(out, 0);                /* maxComponentDepth */
}
