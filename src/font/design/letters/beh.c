#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define TRAY_W 560.0
#define TRAY_LIP 200.0

void body_tooth(Pen *p, Form f)
{
	double tx;
	if (f == FORM_INIT) {
		p->bw = ST + 50;
		tx = p->bw - HS;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      tx, TOOTH, 0,
		      tx, BY, R,
		      0, BY, 0);
	} else {
		p->bw = ST + 60;
		tx = p->bw / 2;
		part_baseline(p, 0, p->bw);
		pen_segment(p, tx, BY, tx, TOOTH);
	}
	pen_anchor_above(p, tx, TOOTH + DOT_CLEAR);
	pen_anchor_below(p, tx, -DOT_CLEAR);
}

void body_beh(Pen *p, Form f)
{
	if (joins_left(f)) {
		body_tooth(p, f);
		return;
	}
	p->bw = TRAY_W;
	double rr = joins_right(f) ? 0 : R;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, TRAY_LIP, 0,
	      HS, BY, R,
	      p->bw - HS, BY, rr,
	      p->bw - HS, TOOTH, 0);
	pen_anchor_above(p, p->bw / 2, ST + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
}
