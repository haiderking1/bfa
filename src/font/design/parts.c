#include "font/design/parts.h"
#include "font/design/style.h"

#include <math.h>

void part_dots(Pen *p, int n, double x, double y, bool above)
{
	double s = above ? 1 : -1;
	double step = DOT_R * 2 + DOT_GAP;
	double row = y + s * DOT_R;
	if (n == 1) {
		pen_disc(p, x, row, DOT_R);
	} else if (n == 2) {
		pen_disc(p, x - step / 2, row, DOT_R);
		pen_disc(p, x + step / 2, row, DOT_R);
	} else if (n == 3) {
		/* the odd dot points away from the letter */
		pen_disc(p, x - step / 2, row, DOT_R);
		pen_disc(p, x + step / 2, row, DOT_R);
		pen_disc(p, x, row + s * step * sin(M_PI / 3), DOT_R);
	}
}

/* drawn on a 0..300 x 0..330 design box, then scaled */
void part_hamza(Pen *p, double x, double y, double height)
{
	double k = height / HAMZA_FULL_H;
	double ox = p->ox, oy = p->oy, sx = p->sx, sy = p->sy, w = p->width;
	p->ox = ox + (x - 150 * k) * sx;
	p->oy = oy + y * sy;
	p->sx = sx * k;
	p->sy = sy * k;
	/* ink width is absolute, the box coords are scaled */
	double sw = height >= HAMZA_FULL_H ? ST : MARK_ST;
	p->width = sw;
	double hw = sw / k / 2;
	/* a c opening right over a foot that runs left */
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      270, 330 - hw, 0,
	      70 + hw, 330 - hw, 90,
	      70 + hw, hw, 0);
	pen_segment(p, 0, hw, 290, hw);
	p->ox = ox;
	p->oy = oy;
	p->sx = sx;
	p->sy = sy;
	p->width = w;
}

void part_madda(Pen *p, double x, double y)
{
	double w = p->width;
	p->width = MARK_ST;
	double hw = MARK_ST / 2;
	pen_move(p, x - 130, y + hw + 10);
	pen_cubic(p, x - 70, y + MADDA_H, x - 40, y + MADDA_H, x, y + MADDA_H / 2);
	pen_cubic(p, x + 40, y + hw, x + 70, y + hw, x + 130, y + MADDA_H - hw);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
	p->width = w;
}

void part_baseline(Pen *p, double x0, double x1)
{
	pen_segment(p, x0, BY, x1, BY);
}
