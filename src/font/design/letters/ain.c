#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define AIN_TOP 360.0
#define AIN_W 360.0

static void bowl(Pen *p, double from_x, double from_y)
{
	double w = p->bw;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      from_x, from_y, 0,
	      HS, -60, 120,
	      HS, DEEP + HS, BOWL_R,
	      w - HS + 10, DEEP + HS, 0);
}

void body_ain(Pen *p, Form f)
{
	double ty = AIN_TOP - HS;
	p->bw = AIN_W;
	double w = p->bw;
	if (f == FORM_INIT) {
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      w - HS, ty - 40, 0,
		      w - 120, ty, 0,
		      HS + 10, ty, 110,
		      HS + 10, BY, 70,
		      w * 0.62, BY, 0);
		part_baseline(p, 0, HS + 20);
	} else if (f == FORM_MEDI || f == FORM_FINA) {
		/* a shield standing on its point */
		double cx = w / 2;
		RPATH_LOOP(p,
			   HS + 20, ty, 100,
			   w - HS - 20, ty, 100,
			   cx, BY, 0);
		if (f == FORM_MEDI)
			part_baseline(p, 0, w);
		else {
			part_baseline(p, cx, w);
			bowl(p, cx, BY);
		}
	} else {
		/* open c on top meeting the bowl at a point */
		double jx = w * 0.62, jy = 90;
		RPATH(p, CAP_FLAT, CAP_FLAT,
		      w - HS, ty - 40, 0,
		      w - 120, ty, 0,
		      HS + 10, ty, 100,
		      HS + 10, jy, 70,
		      jx, jy, 0);
		bowl(p, jx, jy);
	}
	pen_anchor_above(p, w / 2, AIN_TOP + DOT_CLEAR);
	pen_anchor_below(p, w / 2, -DOT_CLEAR);
}
