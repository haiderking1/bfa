#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/style.h"

#define NOON_W 420.0
#define NOON_LIP 230.0

void body_noon(Pen *p, Form f)
{
	if (joins_left(f)) {
		body_tooth(p, f);
		return;
	}
	p->bw = NOON_W;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      HS, NOON_LIP, 0,
	      HS, DESC + HS, BOWL_R,
	      p->bw - HS, DESC + HS, BOWL_R,
	      p->bw - HS, TOOTH, 0);
	pen_anchor_above(p, p->bw / 2, 110);
	pen_anchor_below(p, p->bw / 2, DESC - DOT_CLEAR);
}
