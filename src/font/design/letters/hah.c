#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define HEAD 350.0
#define TICK 90.0
#define HAH_W 470.0

void body_hah(Pen *p, Form f)
{
	double hy = HEAD - HS;
	if (joins_left(f)) {
		/* a hood over the baseline: head on top, drop on the right */
		p->bw = 300;
		double xl = 30 + HS, xr = p->bw - HS;
		double rr = joins_right(f) ? 0 : R;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      xl, hy - TICK, 0,
		      xl, hy, 30,
		      xr, hy, 80,
		      xr, BY, rr,
		      0, BY, 0);
		pen_anchor_above(p, (xl + xr) / 2, HEAD + DOT_CLEAR);
		pen_anchor_below(p, (xl + xr) / 2, -DOT_CLEAR);
		return;
	}
	p->bw = HAH_W;
	double w = p->bw;
	double xl = 60 + HS, xr = w - 80;
	if (f == FORM_FINA) {
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      xl, hy - TICK, 0,
		      xl, hy, 30,
		      xr, hy, 80,
		      xr, BY, 0,
		      HS, BY, 100,
		      HS, DEEP + HS, BOWL_R,
		      w - HS + 10, DEEP + HS, 0);
		part_baseline(p, xr, w);
	} else {
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      xl, hy - TICK, 0,
		      xl, hy, 30,
		      xr, hy, 40,
		      HS, 40, 120,
		      HS, DEEP + HS, BOWL_R,
		      w - HS + 10, DEEP + HS, 0);
	}
	pen_anchor_above(p, (xl + xr) / 2, HEAD + DOT_CLEAR);
	/* the dot of jeem sits in the bowl */
	pen_anchor_below(p, w * 0.55, -70);
}
