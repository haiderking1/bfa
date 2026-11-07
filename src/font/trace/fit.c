#include "font/trace/fit.h"
#include "base/mem.h"

#include <math.h>
#include <stdlib.h>

#define CORNER_DEG 35.0
#define WIN 4.0      /* arc length window for turning angle */
#define LINE_LO 2.0  /* window used to refine a corner's legs */
#define LINE_HI 9.0
#define STRAIGHT_COS 0.9995 /* a line must agree with both end tangents */
#define NEAR_COS 0.995      /* ...unless it is dead straight */

typedef struct {
	const Vec2 *p;
	int n;
} Ring;

static Vec2 at(const Ring *r, int i)
{
	return r->p[((i % r->n) + r->n) % r->n];
}

/* index whose arc distance from i is about d (signed), walking the ring */
static int walk(const Ring *r, int i, double d)
{
	double acc = 0;
	int k = i;
	if (d >= 0) {
		while (acc < d && k - i < r->n - 1) {
			acc += v2_dist(at(r, k), at(r, k + 1));
			k++;
		}
	} else {
		while (acc < -d && i - k < r->n - 1) {
			acc += v2_dist(at(r, k), at(r, k - 1));
			k--;
		}
	}
	return k;
}

static double turn_deg(const Ring *r, int i)
{
	Vec2 a = v2_sub(at(r, i), at(r, walk(r, i, -WIN)));
	Vec2 b = v2_sub(at(r, walk(r, i, WIN)), at(r, i));
	return fabs(atan2(v2_cross(a, b), v2_dot(a, b))) * 180 / M_PI;
}

/* direction of the ring between arc offsets lo..hi from i (lo < hi) */
static Vec2 leg_dir(const Ring *r, int i, double lo, double hi)
{
	return v2_norm(v2_sub(at(r, walk(r, i, hi)), at(r, walk(r, i, lo))));
}

static bool line_x(Vec2 p, Vec2 dp, Vec2 q, Vec2 dq, Vec2 *out, double *tp,
		   double *tq)
{
	double den = v2_cross(dp, dq);
	if (fabs(den) < 1e-9)
		return false;
	Vec2 w = v2_sub(q, p);
	*tp = v2_cross(w, dq) / den;
	*tq = v2_cross(w, dp) / den;
	*out = v2_add(p, v2_scale(dp, *tp));
	return true;
}

/* fitted points stay in doubles until smooth joins are made implicit */
typedef struct {
	Vec2 p;
	bool on, smooth;
} FPt;

typedef struct {
	FPt *p;
	int n, cap;
} Emit;

static void emit(Emit *e, Vec2 p, bool on, bool smooth)
{
	XGROW(e->p, e->cap, e->n + 1);
	e->p[e->n++] = (FPt){p, on, smooth};
}

static void emit_off(Emit *e, Vec2 p) { emit(e, p, false, false); }

static double seg_dist(Vec2 q, Vec2 a, Vec2 b)
{
	Vec2 ab = v2_sub(b, a);
	double l2 = v2_dot(ab, ab);
	double t = l2 > 0 ? v2_dot(v2_sub(q, a), ab) / l2 : 0;
	t = t < 0 ? 0 : t > 1 ? 1 : t;
	return v2_dist(q, v2_add(a, v2_scale(ab, t)));
}

#define QS 48

static double quad_err(const Vec2 *p, int a, int b, Vec2 c, int *worst)
{
	Vec2 s[QS + 1];
	for (int k = 0; k <= QS; k++) {
		double t = (double)k / QS, u = 1 - t;
		s[k] = v2(u * u * p[a].x + 2 * u * t * c.x + t * t * p[b].x,
			  u * u * p[a].y + 2 * u * t * c.y + t * t * p[b].y);
	}
	double maxe = 0;
	*worst = (a + b) / 2;
	for (int i = a + 1; i < b; i++) {
		double e = INFINITY;
		for (int k = 0; k < QS; k++)
			e = fmin(e, seg_dist(p[i], s[k], s[k + 1]));
		if (e > maxe) {
			maxe = e;
			*worst = i;
		}
	}
	return maxe;
}

static double line_err(const Vec2 *p, int a, int b, int *worst)
{
	double maxe = 0;
	*worst = (a + b) / 2;
	for (int i = a + 1; i < b; i++) {
		double e = seg_dist(p[i], p[a], p[b]);
		if (e > maxe) {
			maxe = e;
			*worst = i;
		}
	}
	return maxe;
}

static Vec2 tangent_at(const Vec2 *p, int n, int m)
{
	int lo = m, hi = m;
	double acc = 0;
	while (lo > 0 && acc < 3) {
		acc += v2_dist(p[lo], p[lo - 1]);
		lo--;
	}
	acc = 0;
	while (hi < n - 1 && acc < 3) {
		acc += v2_dist(p[hi], p[hi + 1]);
		hi++;
	}
	return v2_norm(v2_sub(p[hi], p[lo]));
}

typedef struct {
	bool line;
	Vec2 c;
} Piece;

/* one quad (or line) from a to b with the given end tangents */
static bool fit_piece(const Vec2 *p, int a, int b, Vec2 ta, Vec2 tb,
		      double tol, Piece *out)
{
	int worst;
	Vec2 chord_dir = v2_norm(v2_sub(p[b], p[a]));
	double agree = fmin(v2_dot(ta, chord_dir), v2_dot(tb, chord_dir));
	double lerr = line_err(p, a, b, &worst);
	if ((agree > STRAIGHT_COS && lerr <= tol) ||
	    (agree > NEAR_COS && lerr <= tol / 4)) {
		out->line = true;
		return true;
	}
	double sa, sb;
	double chord = v2_dist(p[a], p[b]);
	if (!line_x(p[a], ta, p[b], tb, &out->c, &sa, &sb) || sa <= 0 ||
	    sb >= 0 || sa > 2 * chord || -sb > 2 * chord)
		return false;
	out->line = false;
	return quad_err(p, a, b, out->c, &worst) <= tol;
}

#define MAX_SPLIT 48

/* a curved run in n equal arc-length pieces, the fewest that fit. equal
   pieces give balanced handles, so the joins can become implied. */
static void fit_curve(Emit *e, const Vec2 *p, int a, int b, Vec2 ta, Vec2 tb,
		      double tol, int nall)
{
	double total = 0;
	for (int i = a; i < b; i++)
		total += v2_dist(p[i], p[i + 1]);
	int idx[MAX_SPLIT + 1];
	Vec2 tan[MAX_SPLIT + 1];
	Piece pc[MAX_SPLIT];
	for (int n = 1; n <= MAX_SPLIT; n++) {
		if (n > 1 && (b - a) / n < 3)
			break;
		idx[0] = a;
		tan[0] = ta;
		double acc = 0;
		int i = a;
		for (int k = 1; k < n; k++) {
			while (i < b && acc < total * k / n) {
				acc += v2_dist(p[i], p[i + 1]);
				i++;
			}
			idx[k] = i;
			tan[k] = tangent_at(p, nall, i);
		}
		idx[n] = b;
		tan[n] = tb;
		bool ok = true;
		for (int k = 0; k < n && ok; k++)
			ok = idx[k + 1] > idx[k] &&
			     fit_piece(p, idx[k], idx[k + 1], tan[k], tan[k + 1], tol, &pc[k]);
		if (!ok)
			continue;
		for (int k = 0; k < n; k++) {
			if (!pc[k].line)
				emit_off(e, pc[k].c);
			emit(e, p[idx[k + 1]], true, k + 1 < n);
		}
		return;
	}
	/* nothing fit: fall back to the raw points as lines */
	for (int i = a + 1; i <= b; i++)
		emit(e, p[i], true, false);
}

#define FLAT_CURV 0.0015 /* rad per unit: radius over ~650 counts as flat */
#define MIN_LINE 16.0

/* split a corner-to-corner run into straight lines and curved runs */
static void fit_segment(Emit *e, const Vec2 *p, int n, Vec2 ta, Vec2 tb,
			double tol)
{
	bool *flat = xmalloc((size_t)n * sizeof *flat);
	for (int i = 0; i < n; i++) {
		int lo = i, hi = i;
		double al = 0, ah = 0;
		while (lo > 0 && al < 5) {
			al += v2_dist(p[lo], p[lo - 1]);
			lo--;
		}
		while (hi < n - 1 && ah < 5) {
			ah += v2_dist(p[hi], p[hi + 1]);
			hi++;
		}
		if (al < 2 || ah < 2) {
			flat[i] = true; /* ends lean on the corner tangents */
			continue;
		}
		Vec2 d0 = v2_sub(p[i], p[lo]), d1 = v2_sub(p[hi], p[i]);
		double turn = fabs(atan2(v2_cross(d0, d1), v2_dot(d0, d1)));
		flat[i] = turn / (al + ah) < FLAT_CURV;
	}
	/* straight runs: long flat stretches that really are lines */
	int cur = 0;
	Vec2 tcur = ta;
	int i = 0;
	while (i < n) {
		if (!flat[i]) {
			i++;
			continue;
		}
		int j = i;
		while (j + 1 < n && flat[j + 1])
			j++;
		double len = 0;
		for (int k = i; k < j; k++)
			len += v2_dist(p[k], p[k + 1]);
		int worst;
		if (len >= MIN_LINE && line_err(p, i, j, &worst) <= tol / 2) {
			Vec2 dir = v2_norm(v2_sub(p[j], p[i]));
			if (i > cur)
				fit_curve(e, p, cur, i, tcur, dir, tol, n);
			emit(e, p[j], true, false);
			cur = j;
			tcur = dir;
		}
		i = j + 1;
	}
	if (cur < n - 1)
		fit_curve(e, p, cur, n - 1, tcur, tb, tol, n);
	free(flat);
}

typedef struct {
	int idx;
	Vec2 pos, din, dout;
} Corner;

static int find_corners(const Ring *r, Corner **out)
{
	int n = r->n, cap = 0, nc = 0;
	double *t = xmalloc((size_t)n * sizeof *t);
	for (int i = 0; i < n; i++)
		t[i] = turn_deg(r, i);
	Corner *cs = NULL;
	for (int i = 0; i < n; i++) {
		if (t[i] < CORNER_DEG)
			continue;
		/* keep the strongest point within the window */
		int lo = walk(r, i, -WIN), hi = walk(r, i, WIN);
		bool peak = true;
		for (int k = lo; k <= hi && peak; k++) {
			int kk = ((k % n) + n) % n;
			if (kk == i)
				continue;
			if (t[kk] > t[i] || (t[kk] == t[i] && kk < i))
				peak = false;
		}
		if (!peak)
			continue;
		Corner c = {i, r->p[i], leg_dir(r, i, -LINE_HI, -LINE_LO),
			    leg_dir(r, i, LINE_LO, LINE_HI)};
		Vec2 x;
		double ta, tb;
		Vec2 pin = at(r, walk(r, i, -LINE_LO));
		Vec2 pout = at(r, walk(r, i, LINE_LO));
		if (line_x(pin, c.din, pout, c.dout, &x, &ta, &tb) &&
		    v2_dist(x, r->p[i]) < 6)
			c.pos = x;
		XGROW(cs, cap, nc + 1);
		cs[nc++] = c;
	}
	free(t);
	*out = cs;
	return nc;
}

static Vec2 qpt(Vec2 a, Vec2 c, Vec2 b, double t)
{
	double u = 1 - t;
	return v2(u * u * a.x + 2 * u * t * c.x + t * t * b.x,
		  u * u * a.y + 2 * u * t * c.y + t * t * b.y);
}

/* how far the pair (s,a,m),(m,b,t) strays from (s,a,j),(j,b,t) */
static double implied_err(Vec2 s, Vec2 a, Vec2 j, Vec2 m, Vec2 b, Vec2 t)
{
	enum { N = 24 };
	Vec2 old[2 * N + 1];
	for (int k = 0; k <= N; k++) {
		old[k] = qpt(s, a, j, (double)k / N);
		old[N + k] = qpt(j, b, t, (double)k / N);
	}
	double worst = 0;
	for (int k = 0; k <= N; k++) {
		Vec2 q[2] = {qpt(s, a, m, (double)k / N), qpt(m, b, t, (double)k / N)};
		for (int h = 0; h < 2; h++) {
			double d = INFINITY;
			for (int i = 0; i < 2 * N; i++)
				d = fmin(d, seg_dist(q[h], old[i], old[i + 1]));
			worst = fmax(worst, d);
		}
	}
	return worst;
}

/* the on-curve point a smooth quad pair implies when it is dropped */
static Vec2 on_pos(const FPt *f, int n, int i)
{
	i = ((i % n) + n) % n;
	if (f[i].on)
		return f[i].p;
	return v2_lerp(f[(i - 1 + n) % n].p, f[(i + 1) % n].p, 0.5);
}

/* an on-curve point sitting on the line between two on-curve neighbors
   adds nothing */
static void drop_collinear(OContour *c)
{
	bool changed = true;
	while (changed && c->n > 3) {
		changed = false;
		for (int i = 0; i < c->n && c->n > 3; i++) {
			int n = c->n;
			OPt a = c->p[(i - 1 + n) % n], b = c->p[i], d = c->p[(i + 1) % n];
			if (!a.on || !b.on || !d.on)
				continue;
			double dx = d.x - a.x, dy = d.y - a.y;
			double len = hypot(dx, dy);
			bool dup = (b.x == a.x && b.y == a.y) || (b.x == d.x && b.y == d.y);
			double off = len > 0 ? fabs(dx * (b.y - a.y) - dy * (b.x - a.x)) / len : 0;
			double along = dx * (b.x - a.x) + dy * (b.y - a.y);
			if (dup || (off < 0.5 && along > 0 && along < len * len)) {
				for (int k = i; k + 1 < n; k++)
					c->p[k] = c->p[k + 1];
				c->n--;
				changed = true;
			}
		}
	}
}

static void finish(const Emit *e, double tol, OContour *c)
{
	int n = e->n;
	FPt *f = xmalloc((size_t)n * sizeof *f);
	for (int i = 0; i < n; i++)
		f[i] = e->p[i];
	/* the last point is the ring's start: it stays on-curve as an anchor */
	for (int i = 0; i < n - 1; i++) {
		int ip = (i - 1 + n) % n, in = (i + 1) % n;
		if (!f[i].on || !f[i].smooth || f[ip].on || f[in].on)
			continue;
		/* round the controls first: the midpoint of two integer
		   points is what the rasterizer will actually use */
		Vec2 a = v2(round(f[ip].p.x), round(f[ip].p.y));
		Vec2 b = v2(round(f[in].p.x), round(f[in].p.y));
		Vec2 m = v2_lerp(a, b, 0.5);
		Vec2 s = on_pos(f, n, ip - 1), t = on_pos(f, n, in + 1);
		if (implied_err(s, f[ip].p, f[i].p, m, f[in].p, t) <= tol) {
			f[i].on = false;
			f[i].smooth = false;
			f[i].p = v2(NAN, NAN);
		}
	}
	for (int i = 0; i < n; i++)
		if (!isnan(f[i].p.x))
			contour_push(c, (int)lround(f[i].p.x),
				     (int)lround(f[i].p.y), f[i].on);
	free(f);
	drop_collinear(c);
}

void fit_loop(const Poly *loop, double tol, Outline *out)
{
	Ring r = {loop->p, loop->n};
	if (r.n < 3)
		return;
	Corner *cs;
	int nc = find_corners(&r, &cs);
	Emit e = {0};
	Vec2 *buf = xmalloc((size_t)(r.n + 2) * sizeof *buf);

	if (nc == 0) {
		int n = 0;
		for (int i = 0; i <= r.n; i++)
			buf[n++] = at(&r, i);
		Vec2 t0 = v2_norm(v2_sub(at(&r, walk(&r, 0, 3)), at(&r, walk(&r, 0, -3))));
		fit_segment(&e, buf, n, t0, t0, tol);
		e.p[e.n - 1].smooth = true;
	} else {
		for (int k = 0; k < nc; k++) {
			Corner *c0 = &cs[k], *c1 = &cs[(k + 1) % nc];
			int end = c1->idx;
			if (end <= c0->idx)
				end += r.n;
			int n = 0;
			buf = xrealloc(buf, (size_t)(end - c0->idx + 2) * sizeof *buf);
			buf[n++] = c0->pos;
			for (int i = c0->idx + 1; i < end; i++)
				buf[n++] = at(&r, i);
			buf[n++] = c1->pos;
			fit_segment(&e, buf, n, c0->dout, c1->din, tol);
		}
	}
	/* every piece emitted its end point, so the loop already closes on
	   the start: the emitted list is the whole ring */
	OContour *c = outline_add(out);
	finish(&e, tol, c);
	if (c->n < 3) {
		free(c->p);
		out->n--;
	}
	free(e.p);
	free(buf);
	free(cs);
}
