#include "font/design/letters/letters.h"
#include "font/design/letters/loop.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define SAD_LOOP_W 320.0
#define SAD_LOOP_H 300.0
#define SAD_TOOTH_GAP 110.0
#define SAD_BOWL_W 380.0
#define SAD_LIP 190.0

void body_sad(Pen *p, Form f)
{
	double bowl = joins_left(f) ? 0 : SAD_BOWL_W;
	double tx = joins_left(f) ? 20 + HS : bowl - HS;
	double lx0 = tx + SAD_TOOTH_GAP - HS;
	p->bw = lx0 + SAD_LOOP_W;
	loop_flat(p, lx0, p->bw, SAD_LOOP_H, 120);
	pen_segment(p, tx, BY, tx, TOOTH - 40);
	if (joins_left(f)) {
		part_baseline(p, 0, lx0 + 60);
	} else {
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      HS, SAD_LIP, 0,
		      HS, DESC + HS, BOWL_R,
		      tx, DESC + HS, BOWL_R,
		      tx, BY, 0);
		part_baseline(p, tx - 1, lx0 + 60);
	}
	if (joins_right(f))
		part_baseline(p, lx0 + 60, p->bw);
	pen_anchor_above(p, lx0 + SAD_LOOP_W / 2, SAD_LOOP_H + DOT_CLEAR);
	pen_anchor_below(p, lx0 + SAD_LOOP_W / 2, -DOT_CLEAR);
}
