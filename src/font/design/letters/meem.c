#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define MEEM_RX 96.0
#define MEEM_RY 92.0

void body_meem(Pen *p, Form f)
{
	double lead = joins_left(f) ? 30 : 0;
	p->bw = lead + 2 * MEEM_RX + ST;
	double cx = lead + HS + MEEM_RX, cy = BY + MEEM_RY;
	pen_ring(p, cx, cy, MEEM_RX, MEEM_RY);
	if (joins_left(f))
		part_baseline(p, 0, cx);
	if (joins_right(f))
		part_baseline(p, cx, p->bw);
	if (!joins_left(f))
		pen_segment(p, cx - MEEM_RX, cy, cx - MEEM_RX, DESC);
	pen_anchor_above(p, cx, cy + MEEM_RY + HS + DOT_CLEAR);
	pen_anchor_below(p, cx, -DOT_CLEAR);
}
