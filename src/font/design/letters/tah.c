#include "font/design/letters/letters.h"
#include "font/design/letters/loop.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define TAH_W 400.0
#define TAH_LOOP_H 300.0

void body_tah(Pen *p, Form f)
{
	double x0 = joins_left(f) ? 20 : 0;
	p->bw = x0 + TAH_W;
	/* the stem rises straight out of the loop's left wall */
	double a = x0 + HS, b = p->bw - HS, t = TAH_LOOP_H - HS;
	RPATH_LOOP(p,
		   a, BY, 50,
		   b, BY, 110,
		   b, t, 110,
		   a, t, 0);
	pen_segment(p, a, BY, a, TOP);
	if (joins_left(f))
		part_baseline(p, 0, x0 + 100);
	if (joins_right(f))
		part_baseline(p, p->bw - 100, p->bw);
	pen_anchor_above(p, a + 150, TAH_LOOP_H + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
}
