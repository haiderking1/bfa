#include "font/ink/field.h"
#include "base/mem.h"

#include <math.h>
#include <stdlib.h>

void field_init(Field *f, double xmin, double ymin, double xmax, double ymax,
		double step)
{
	f->step = step;
	f->x0 = floor(xmin / step) * step;
	f->y0 = floor(ymin / step) * step;
	f->nx = (int)ceil((xmax - f->x0) / step) + 1;
	f->ny = (int)ceil((ymax - f->y0) / step) + 1;
	long n = (long)f->nx * f->ny;
	f->d = xmalloc((size_t)n * sizeof *f->d);
	for (long k = 0; k < n; k++)
		f->d[k] = 1e9f;
}

void field_free(Field *f)
{
	free(f->d);
	f->d = NULL;
}
