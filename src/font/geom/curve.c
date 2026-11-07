#include "font/geom/curve.h"

#include <math.h>

static int steps_for(double dev, double tol)
{
	int n = (int)ceil(sqrt(dev / tol));
	return n < 1 ? 1 : n > 512 ? 512 : n;
}

void curve_quad(Poly *out, Vec2 p0, Vec2 c, Vec2 p1, double tol)
{
	double dev = v2_len(v2_add(v2_sub(p0, v2_scale(c, 2)), p1)) / 4;
	int n = steps_for(dev, tol);
	for (int i = 1; i <= n; i++) {
		double t = (double)i / n, u = 1 - t;
		poly_push(out, v2(u * u * p0.x + 2 * u * t * c.x + t * t * p1.x,
				  u * u * p0.y + 2 * u * t * c.y + t * t * p1.y));
	}
}

void curve_cubic(Poly *out, Vec2 p0, Vec2 c1, Vec2 c2, Vec2 p1, double tol)
{
	double d1 = v2_len(v2_add(v2_sub(p0, v2_scale(c1, 2)), c2));
	double d2 = v2_len(v2_add(v2_sub(c1, v2_scale(c2, 2)), p1));
	int n = steps_for(0.75 * fmax(d1, d2), tol);
	for (int i = 1; i <= n; i++) {
		double t = (double)i / n, u = 1 - t;
		double a = u * u * u, b = 3 * u * u * t, cc = 3 * u * t * t, d = t * t * t;
		poly_push(out, v2(a * p0.x + b * c1.x + cc * c2.x + d * p1.x,
				  a * p0.y + b * c1.y + cc * c2.y + d * p1.y));
	}
}

void curve_arc(Poly *out, Vec2 center, double rx, double ry, double a0,
	       double a1, double tol)
{
	double r = fmax(rx, ry);
	double step = r > tol ? 2 * acos(1 - tol / r) : M_PI / 4;
	int n = (int)ceil(fabs(a1 - a0) / step);
	if (n < 1)
		n = 1;
	for (int i = 0; i <= n; i++) {
		double a = a0 + (a1 - a0) * i / n;
		poly_push(out, v2(center.x + rx * cos(a), center.y + ry * sin(a)));
	}
}
