#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define LA_W 380.0

void body_lamalef(Pen *p, Form f)
{
	p->bw = LA_W;
	double x = p->bw - HS;
	double foot = p->bw - 190;
	double rr = joins_right(f) ? 0 : R;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x, TOP, 0,
	      x, BY, rr,
	      foot, BY, 0);
	/* the alef leans in to meet the foot */
	pen_segment(p, HS + 10, TOP, foot + HS, BY - 2);
	pen_anchor_above(p, HS + 30, TOP + DOT_CLEAR);
	pen_anchor_below(p, foot + 10, -DOT_CLEAR);
}
