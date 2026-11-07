#ifndef BFA_TESTS_OUTLINE_UTIL_H
#define BFA_TESTS_OUTLINE_UTIL_H

#include "font/outline/outline.h"

#include <math.h>

/* signed area of the on/off polygon; negative is clockwise (y up) */
static inline double contour_area(const OContour *c)
{
	double a = 0;
	for (int i = 0; i < c->n; i++) {
		OPt p = c->p[i], q = c->p[(i + 1) % c->n];
		a += (double)p.x * q.y - (double)q.x * p.y;
	}
	return a / 2;
}

/* rendered point on the contour at param t of the segment that starts at
   index i; walks implied on-curve midpoints like a rasterizer */
static inline double contour_max_radial_err(const OContour *c, double cx,
					    double cy, double r)
{
	double worst = 0;
	int n = c->n;
	for (int j = 0; j < n; j++) {
		OPt p = c->p[j];
		if (p.on)
			continue;
		OPt a = c->p[(j - 1 + n) % n], b = c->p[(j + 1) % n];
		double ax = a.on ? a.x : (a.x + p.x) / 2.0;
		double ay = a.on ? a.y : (a.y + p.y) / 2.0;
		double bx = b.on ? b.x : (b.x + p.x) / 2.0;
		double by = b.on ? b.y : (b.y + p.y) / 2.0;
		for (int s = 0; s <= 32; s++) {
			double t = s / 32.0, u = 1 - t;
			double x = u * u * ax + 2 * u * t * p.x + t * t * bx;
			double y = u * u * ay + 2 * u * t * p.y + t * t * by;
			double e = fabs(hypot(x - cx, y - cy) - r);
			if (e > worst)
				worst = e;
		}
	}
	return worst;
}

#endif
