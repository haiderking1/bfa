#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define HEH_W 300.0
#define HEH_H 350.0
#define ARCH_W 330.0
#define ARCH_H 390.0
#define FINA_R 92.0
#define FINA_STEM 360.0

void body_heh(Pen *p, Form f)
{
	if (joins_left(f)) {
		/* an arch over the baseline with a small eye inside */
		p->bw = ARCH_W;
		double w = p->bw;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      HS, BY, 0,
		      HS, ARCH_H - HS, 150,
		      w - HS, ARCH_H - HS, 150,
		      w - HS, BY, 0);
		part_baseline(p, 0, w);
		pen_ring(p, HS + 95, BY + 85, 62, 72);
		pen_anchor_above(p, w / 2, ARCH_H + DOT_CLEAR);
		pen_anchor_below(p, w / 2, -DOT_CLEAR);
		return;
	}
	if (f == FORM_FINA) {
		p->bw = 2 * FINA_R + ST + 10;
		double cx = HS + FINA_R, cy = BY + FINA_R;
		pen_ring(p, cx, cy, FINA_R, FINA_R);
		double sx = p->bw - HS;
		pen_segment(p, sx, BY, sx, FINA_STEM);
		part_baseline(p, cx, p->bw);
		pen_anchor_above(p, cx + 20, FINA_STEM + DOT_CLEAR);
		pen_anchor_below(p, cx, -DOT_CLEAR);
		return;
	}
	p->bw = HEH_W;
	RLOOP(p, 120,
	      HS, BY,
	      p->bw - HS, BY,
	      p->bw - HS, HEH_H - HS,
	      HS, HEH_H - HS);
	pen_anchor_above(p, p->bw / 2, HEH_H + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
}
