#include "font/design/letters/letters.h"
#include "font/design/style.h"

#define REH_W 250.0
#define REH_H 220.0

void body_reh(Pen *p, Form f)
{
	(void)f;
	p->bw = REH_W;
	double x = p->bw - HS;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x, REH_H, 0,
	      x, DESC + HS, 120,
	      0, DESC + HS, 0);
	pen_anchor_above(p, x, REH_H + DOT_CLEAR);
	pen_anchor_below(p, x * 0.5, DESC - DOT_CLEAR);
}
