#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define LAM_W 360.0
#define LAM_LIP 170.0

void body_lam(Pen *p, Form f)
{
	if (f == FORM_INIT) {
		p->bw = ST + 50;
		double x = p->bw - HS;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      x, TOP, 0,
		      x, BY, R,
		      0, BY, 0);
		pen_anchor_above(p, x, TOP + DOT_CLEAR);
		pen_anchor_below(p, x, -DOT_CLEAR);
		return;
	}
	if (f == FORM_MEDI) {
		p->bw = ST + 60;
		double x = p->bw / 2;
		part_baseline(p, 0, p->bw);
		pen_segment(p, x, BY, x, TOP);
		pen_anchor_above(p, x, TOP + DOT_CLEAR);
		pen_anchor_below(p, x, -DOT_CLEAR);
		return;
	}
	p->bw = LAM_W;
	double x = p->bw - HS;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x, TOP, 0,
	      x, DESC + HS, BOWL_R,
	      HS, DESC + HS, BOWL_R,
	      HS, LAM_LIP, 0);
	pen_anchor_above(p, x, TOP + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, DESC - DOT_CLEAR);
}
