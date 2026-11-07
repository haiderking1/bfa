#include "font/design/letters/letters.h"
#include "font/design/letters/loop.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define HEAD_W 230.0
#define HEAD_H 300.0
#define FEH_W 580.0
#define QAF_W 440.0
#define FEH_LIP 200.0

/* the head loop sits at the right end of the body */
static double head(Pen *p)
{
	double hx0 = p->bw - HEAD_W;
	loop_flat(p, hx0, p->bw, HEAD_H, 90);
	pen_anchor_above(p, hx0 + HEAD_W / 2, HEAD_H + DOT_CLEAR);
	return hx0;
}

void body_feh(Pen *p, Form f)
{
	if (joins_left(f)) {
		p->bw = HEAD_W + 20;
		double hx0 = head(p);
		part_baseline(p, 0, joins_right(f) ? p->bw : hx0 + 60);
		pen_anchor_below(p, hx0 + HEAD_W / 2, -DOT_CLEAR);
		return;
	}
	p->bw = FEH_W;
	double hx0 = head(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, FEH_LIP, 0,
	      HS, BY, R,
	      hx0 + 60, BY, 0);
	if (joins_right(f))
		part_baseline(p, hx0, p->bw);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
}

void body_qaf(Pen *p, Form f)
{
	if (joins_left(f)) {
		body_feh(p, f);
		return;
	}
	p->bw = QAF_W;
	double hx0 = head(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, FEH_LIP, 0,
	      HS, DESC + HS, BOWL_R,
	      hx0 + HS, DESC + HS, BOWL_R,
	      hx0 + HS, BY + 40, 0);
	if (joins_right(f))
		part_baseline(p, hx0, p->bw);
	pen_anchor_below(p, p->bw / 2, DESC - DOT_CLEAR);
}
