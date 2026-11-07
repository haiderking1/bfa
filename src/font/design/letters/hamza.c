#include "font/design/letters/letters.h"
#include "font/design/parts.h"
#include "font/design/style.h"

void body_hamza(Pen *p, Form f)
{
	(void)f;
	p->bw = 300 * (HAMZA_FULL_H * 0.8 / HAMZA_FULL_H);
	part_hamza(p, p->bw / 2, 0, HAMZA_FULL_H * 0.8);
	pen_anchor_above(p, p->bw / 2, HAMZA_FULL_H * 0.8 + DOT_CLEAR);
	pen_anchor_below(p, p->bw / 2, -DOT_CLEAR);
}
