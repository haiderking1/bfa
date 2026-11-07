#include "font/geom/fillet.h"
#include "font/geom/curve.h"

#include <math.h>

static void corner(Poly *out, Vec2 a, Vec2 v, Vec2 b, double r, double lim_in,
		   double lim_out, double tol)
{
	Vec2 din = v2_norm(v2_sub(v, a)), dout = v2_norm(v2_sub(b, v));
	double turn = atan2(v2_cross(din, dout), v2_dot(din, dout));
	if (fabs(turn) < 1e-6 || r <= 0) {
		poly_push(out, v);
		return;
	}
	double half = fabs(turn) / 2;
	double t = r * tan(half);
	double lim = fmin(lim_in, lim_out);
	if (t > lim) {
		t = lim;
		r = t / tan(half);
	}
	Vec2 p = v2_sub(v, v2_scale(din, t));
	Vec2 nrm = turn > 0 ? v2_perp(din) : v2_scale(v2_perp(din), -1);
	Vec2 c = v2_add(p, v2_scale(nrm, r));
	double a0 = atan2(p.y - c.y, p.x - c.x);
	double a1 = a0 + turn;
	curve_arc(out, c, r, r, a0, a1, tol);
}

void fillet(Poly *out, const Vec2 *v, const double *radii, int n, double r,
	    int closed, double tol)
{
	if (n < 3) {
		for (int i = 0; i < n; i++)
			poly_push(out, v[i]);
		return;
	}
	if (!closed)
		poly_push(out, v[0]);
	int first = closed ? 0 : 1, last = closed ? n : n - 1;
	for (int i = first; i < last; i++) {
		int ia = (i - 1 + n) % n, ib = (i + 1) % n;
		double lin = v2_dist(v[ia], v[i]), lout = v2_dist(v[i], v[ib]);
		/* a leg shared with another rounded corner only gets half */
		double lim_in = (!closed && ia == 0) ? lin : lin / 2;
		double lim_out = (!closed && ib == n - 1) ? lout : lout / 2;
		corner(out, v[ia], v[i], v[ib], radii ? radii[i] : r, lim_in, lim_out,
		       tol);
	}
	if (!closed)
		poly_push(out, v[n - 1]);
}
