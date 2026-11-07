#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define KAF_W 470.0
#define KAF_LIP 200.0
#define ELBOW_Y 330.0   /* where the joined stem bends back */
#define ELBOW_DX 130.0
#define FLAG_DY 150.0   /* gaf's second stroke sits this far above */

/* joined kaf: a stem that bends left then shoots up and right */
static void joined(Pen *p, Form f, bool gaf)
{
	p->bw = ST + ELBOW_DX + 40;
	double x = p->bw - HS;
	double rr = joins_right(f) ? 0 : R;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      0, BY, 0,
	      x, BY, rr,
	      x, ELBOW_Y, 60,
	      x - ELBOW_DX, ELBOW_Y + 120, 60,
	      x + 10, TOP - 20, 0);
	if (joins_right(f))
		part_baseline(p, x, p->bw);
	if (gaf)
		pen_segment(p, x - ELBOW_DX + 50, ELBOW_Y + 120 + FLAG_DY + 30,
			    x + 40, TOP - 20 + FLAG_DY);
	pen_anchor_above(p, x, TOP + FLAG_DY + DOT_CLEAR);
	pen_anchor_below(p, x - 40, -DOT_CLEAR);
}

/* final kaf: a tray with a tall stem on the right */
static double tray(Pen *p, Form f, double stem_top)
{
	p->bw = KAF_W;
	double x = p->bw - HS;
	double rr = joins_right(f) ? 0 : R;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, KAF_LIP, 0,
	      HS, BY, R,
	      x, BY, rr,
	      x, stem_top, 0);
	pen_anchor_above(p, x, TOP + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
	return x;
}

void body_kaf(Pen *p, Form f)
{
	if (joins_left(f)) {
		joined(p, f, false);
		return;
	}
	tray(p, f, TOP);
	/* the little hamza-like stroke inside */
	part_hamza(p, p->bw / 2 - 10, ST + 70, 180);
}

static void keheh_top(Pen *p, Form f, bool gaf)
{
	double stem = TOP - 160;
	double x = tray(p, f, stem);
	pen_segment(p, x + HS * 0.6, stem - 30, x - 230, TOP);
	if (gaf)
		pen_segment(p, x + HS * 0.6, stem - 30 + FLAG_DY, x - 230, TOP + FLAG_DY);
}

void body_keheh(Pen *p, Form f)
{
	if (joins_left(f))
		joined(p, f, false);
	else
		keheh_top(p, f, false);
}

void body_gaf(Pen *p, Form f)
{
	if (joins_left(f))
		joined(p, f, true);
	else
		keheh_top(p, f, true);
}
