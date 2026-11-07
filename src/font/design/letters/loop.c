#include "font/design/letters/loop.h"
#include "font/design/style.h"

void loop_flat(Pen *p, double x0, double x1, double top, double r)
{
	double a = x0 + HS, b = x1 - HS, t = top - HS;
	RLOOP(p, r, a, BY, b, BY, b, t, a, t);
}
