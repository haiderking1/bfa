#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define TEETH_GAP 130.0
#define BOWL_W 380.0
#define SEEN_LIP 190.0

/* three teeth starting at x0 (left tooth) on a baseline running to x1 */
static void teeth(Pen *p, double x0, double x1, Form f, bool left_tooth)
{
	double xr = x0 + 2 * TEETH_GAP;
	double rr = joins_right(f) ? 0 : R;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x1, BY, 0,
	      xr, BY, rr,
	      xr, SEEN_TOOTH, 0);
	if (joins_right(f) && x1 < p->bw)
		part_baseline(p, xr, p->bw);
	pen_segment(p, x0 + TEETH_GAP, BY, x0 + TEETH_GAP, SEEN_TOOTH);
	if (left_tooth)
		pen_segment(p, x0, BY, x0, SEEN_TOOTH);
}

void body_seen(Pen *p, Form f)
{
	if (joins_left(f)) {
		p->bw = 2 * TEETH_GAP + ST + 10;
		double x0 = 10 + HS;
		teeth(p, x0, 0, f, true);
		if (joins_right(f))
			part_baseline(p, 0, p->bw);
		pen_anchor_above(p, x0 + TEETH_GAP, SEEN_TOOTH + DOT_CLEAR);
		pen_anchor_below(p, x0 + TEETH_GAP, -DOT_CLEAR);
		return;
	}
	p->bw = BOWL_W + 2 * TEETH_GAP + HS;
	double x0 = BOWL_W - HS;
	/* the bowl's right wall rises on to become the first tooth */
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, SEEN_LIP, 0,
	      HS, DESC + HS, BOWL_R,
	      x0, DESC + HS, BOWL_R,
	      x0, SEEN_TOOTH, 0);
	teeth(p, x0, x0, f, false);
	if (joins_right(f))
		part_baseline(p, x0, p->bw);
	pen_anchor_above(p, x0 + TEETH_GAP, SEEN_TOOTH + DOT_CLEAR);
	pen_anchor_below(p, BOWL_W / 2, DESC - DOT_CLEAR);
}
