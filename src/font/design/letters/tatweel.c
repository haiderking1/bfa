#include "font/design/letters/letters.h"
#include "font/design/parts.h"
#include "font/design/style.h"

void body_tatweel(Pen *p, Form f)
{
	(void)f;
	p->bw = 200;
	part_baseline(p, 0, p->bw);
}
