#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/style.h"

#define DAL_W 290.0
#define DAL_H 370.0
#define DAL_SLANT 130.0

void body_dal(Pen *p, Form f)
{
	p->bw = DAL_W;
	double w = p->bw, ty = DAL_H - HS;
	double rr = joins_right(f) ? 0 : R;
	/* a leaning cap stroke falling into the wall */
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS + 30, ty, 0,
	      w - HS, ty - DAL_SLANT, 40,
	      w - HS, BY, rr,
	      0, BY, 0);
	pen_anchor_above(p, w * 0.55, DAL_H + DOT_CLEAR);
	pen_anchor_below(p, w * 0.5, -DOT_CLEAR);
}
