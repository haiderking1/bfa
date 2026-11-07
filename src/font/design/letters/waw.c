#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/style.h"

#define WAW_R 92.0

void body_waw(Pen *p, Form f)
{
	(void)f;
	p->bw = 2 * WAW_R + ST;
	double cx = HS + WAW_R, cy = BY + WAW_R;
	double x = p->bw - HS;
	pen_ring(p, cx, cy, WAW_R, WAW_R);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x, cy, 0,
	      x, DESC + HS, 120,
	      -40, DESC + HS, 0);
	pen_anchor_above(p, cx, cy + WAW_R + HS + DOT_CLEAR);
	pen_anchor_below(p, cx, DESC - DOT_CLEAR);
}
