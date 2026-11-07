#include "font/design/letters/letters.h"
#include "font/design/style.h"

void body_alef(Pen *p, Form f)
{
	if (f == FORM_FINA) {
		p->bw = ST + 40;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      HS, TOP, 0,
		      HS, BY, R,
		      p->bw, BY, 0);
	} else {
		p->bw = ST;
		pen_segment(p, HS, 0, HS, TOP);
	}
	pen_anchor_above(p, HS, TOP + DOT_CLEAR);
	pen_anchor_below(p, HS, -DOT_CLEAR);
}
