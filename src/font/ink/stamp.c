#include "font/ink/stamp.h"
#include "base/mem.h"

#include <math.h>
#include <stdlib.h>

typedef struct {
	int i0, j0, i1, j1;
} Range;

static Range range_of(const Field *f, double xmin, double ymin, double xmax,
		      double ymax)
{
	Range g;
	g.i0 = (int)floor((xmin - f->x0) / f->step);
	g.j0 = (int)floor((ymin - f->y0) / f->step);
	g.i1 = (int)ceil((xmax - f->x0) / f->step);
	g.j1 = (int)ceil((ymax - f->y0) / f->step);
	if (g.i0 < 0) g.i0 = 0;
	if (g.j0 < 0) g.j0 = 0;
	if (g.i1 > f->nx - 1) g.i1 = f->nx - 1;
	if (g.j1 > f->ny - 1) g.j1 = f->ny - 1;
	return g;
}

void stamp_disc(Field *f, Vec2 c, double r)
{
	double m = r + 2 * f->step;
	Range g = range_of(f, c.x - m, c.y - m, c.x + m, c.y + m);
	for (int j = g.j0; j <= g.j1; j++)
		for (int i = g.i0; i <= g.i1; i++) {
			Vec2 p = v2(f->x0 + i * f->step, f->y0 + j * f->step);
			float d = (float)(v2_dist(p, c) - r);
			float *dst = field_at(f, i, j);
			if (d < *dst)
				*dst = d;
		}
}

/* distance to the polyline as a whole, so round joins never poke past a
   flat cap: only the endpoint itself can produce a capped value */
void stamp_stroke(Field *f, const Vec2 *p, int n, bool closed, double r,
		  Cap c0, Cap c1)
{
	double m = r + 2 * f->step;
	double bx0 = INFINITY, by0 = INFINITY, bx1 = -INFINITY, by1 = -INFINITY;
	for (int k = 0; k < n; k++) {
		bx0 = fmin(bx0, p[k].x); by0 = fmin(by0, p[k].y);
		bx1 = fmax(bx1, p[k].x); by1 = fmax(by1, p[k].y);
	}
	Range g = range_of(f, bx0 - m, by0 - m, bx1 + m, by1 + m);
	int w = g.i1 - g.i0 + 1, h = g.j1 - g.j0 + 1;
	if (w <= 0 || h <= 0)
		return;
	float *best = xmalloc((size_t)w * h * sizeof *best);
	float *capv = xmalloc((size_t)w * h * sizeof *capv);
	for (long q = 0; q < (long)w * h; q++) {
		best[q] = INFINITY;
		capv[q] = NAN;
	}
	int nseg = closed ? n : n - 1;
	for (int k = 0; k < nseg; k++) {
		Vec2 a = p[k], b = p[(k + 1) % n];
		Vec2 ab = v2_sub(b, a);
		double len2 = v2_dot(ab, ab);
		if (len2 < 1e-18)
			continue;
		double len = sqrt(len2);
		Vec2 u = v2_scale(ab, 1 / len);
		bool flat0 = !closed && k == 0 && c0 == CAP_FLAT;
		bool flat1 = !closed && k == nseg - 1 && c1 == CAP_FLAT;
		Range s = range_of(f, fmin(a.x, b.x) - m, fmin(a.y, b.y) - m,
				   fmax(a.x, b.x) + m, fmax(a.y, b.y) + m);
		for (int j = s.j0; j <= s.j1; j++)
			for (int i = s.i0; i <= s.i1; i++) {
				Vec2 q = v2(f->x0 + i * f->step, f->y0 + j * f->step);
				Vec2 aq = v2_sub(q, a);
				double t = v2_dot(aq, ab) / len2;
				double tc = t < 0 ? 0 : t > 1 ? 1 : t;
				double d = v2_dist(q, v2_add(a, v2_scale(ab, tc)));
				long o = (long)(j - g.j0) * w + (i - g.i0);
				if (d >= best[o])
					continue;
				best[o] = (float)d;
				/* near a flat end the field is a box's: the side
				   distance against the cap plane, on both sides of
				   the plane so it stays continuous across it */
				double perp = fabs(v2_cross(u, aq));
				bool at0 = flat0 && t <= 1, at1 = flat1 && t >= 0;
				if (at0 || at1) {
					double v = perp - r;
					if (at0)
						v = fmax(v, -t * len);
					if (at1)
						v = fmax(v, (t - 1) * len);
					capv[o] = (float)v;
				} else {
					capv[o] = NAN;
				}
			}
	}
	for (int j = 0; j < h; j++)
		for (int i = 0; i < w; i++) {
			long o = (long)j * w + i;
			if (!isfinite(best[o]))
				continue;
			float v = isnan(capv[o]) ? best[o] - (float)r : capv[o];
			float *dst = field_at(f, g.i0 + i, g.j0 + j);
			if (v < *dst)
				*dst = v;
		}
	free(best);
	free(capv);
}
