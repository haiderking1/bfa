#include "font/trace/trace.h"
#include "font/trace/fit.h"
#include "font/trace/march.h"

void trace_ink(const Ink *k, double step, double tol, Outline *out)
{
	double box[4];
	if (!ink_bbox(k, box))
		return;
	double m = 4 * step;
	Field f;
	field_init(&f, box[0] - m, box[1] - m, box[2] + m, box[3] + m, step);
	ink_render(k, &f);
	Loops loops = {0};
	march(&f, &loops);
	for (int i = 0; i < loops.n; i++)
		fit_loop(&loops.loop[i], tol, out);
	loops_free(&loops);
	field_free(&f);
}
