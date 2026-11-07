#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/style.h"

#define YEH_W 500.0
#define YEH_HOOK 270.0

void body_yeh(Pen *p, Form f)
{
	if (joins_left(f)) {
		body_tooth(p, f);
		return;
	}
	p->bw = YEH_W;
	double w = p->bw;
	if (f == FORM_FINA) {
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      w, BY, 0,
		      HS, BY, 110,
		      HS, DESC + HS, BOWL_R,
		      w - HS, DESC + HS, 90,
		      w - HS, -150, 0);
	} else {
		/* a diagonal falls into the left wall of the bowl */
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      w - HS - 20, YEH_HOOK, 0,
		      HS, 10, 160,
		      HS, DESC + HS, BOWL_R,
		      w - HS, DESC + HS, 90,
		      w - HS, -150, 0);
	}
	pen_anchor_below(p, w * 0.5, DESC - DOT_CLEAR);
	pen_anchor_above(p, w * 0.7, YEH_HOOK + DOT_CLEAR - 30);
}
