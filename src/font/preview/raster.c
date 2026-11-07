#include "font/preview/raster.h"
#include "base/mem.h"
#include "base/vec.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#define SUB 5

typedef struct {
	double x0, y0, x1, y1;
	int dir;
} Edge;

typedef struct {
	Edge *e;
	int n, cap;
} Edges;

static void add_line(Edges *es, Vec2 a, Vec2 b)
{
	if (a.y == b.y)
		return;
	XGROW(es->e, es->cap, es->n + 1);
	es->e[es->n++] = a.y < b.y ? (Edge){a.x, a.y, b.x, b.y, 1}
				   : (Edge){b.x, b.y, a.x, a.y, -1};
}

static void add_quad(Edges *es, Vec2 a, Vec2 c, Vec2 b)
{
	int n = 12;
	Vec2 prev = a;
	for (int i = 1; i <= n; i++) {
		double t = (double)i / n, u = 1 - t;
		Vec2 p = v2(u * u * a.x + 2 * u * t * c.x + t * t * b.x,
			    u * u * a.y + 2 * u * t * c.y + t * t * b.y);
		add_line(es, prev, p);
		prev = p;
	}
}

static Vec2 xf(OPt p, double s, double ox, double oy)
{
	return v2(ox + p.x * s, oy - p.y * s);
}

static void flatten(Edges *es, const OContour *c, double s, double ox, double oy)
{
	int n = c->n, start = -1;
	for (int i = 0; i < n; i++)
		if (c->p[i].on) {
			start = i;
			break;
		}
	Vec2 first, cur;
	if (start < 0) {
		/* all off-curve: start at an implied midpoint */
		first = v2_lerp(xf(c->p[0], s, ox, oy), xf(c->p[1], s, ox, oy), 0.5);
		start = 0;
	} else {
		first = xf(c->p[start], s, ox, oy);
		start++;
	}
	cur = first;
	bool have_ctrl = false;
	Vec2 ctrl = {0, 0};
	for (int k = 0; k < n; k++) {
		OPt p = c->p[(start + k) % n];
		Vec2 v = xf(p, s, ox, oy);
		if (p.on) {
			if (have_ctrl)
				add_quad(es, cur, ctrl, v);
			else
				add_line(es, cur, v);
			cur = v;
			have_ctrl = false;
		} else {
			if (have_ctrl) {
				Vec2 mid = v2_lerp(ctrl, v, 0.5);
				add_quad(es, cur, ctrl, mid);
				cur = mid;
			}
			ctrl = v;
			have_ctrl = true;
		}
	}
	if (have_ctrl)
		add_quad(es, cur, ctrl, first);
	else
		add_line(es, cur, first);
}

typedef struct {
	double x;
	int dir;
} Hit;

static int hit_cmp(const void *a, const void *b)
{
	double d = ((const Hit *)a)->x - ((const Hit *)b)->x;
	return d < 0 ? -1 : d > 0;
}

void raster_outline(Image *im, const Outline *o, double scale, double ox,
		    double oy)
{
	Edges es = {0};
	for (int i = 0; i < o->n; i++)
		flatten(&es, &o->c[i], scale, ox, oy);
	float *row = xmalloc((size_t)(im->w + 2) * sizeof *row);
	Hit *hits = xmalloc((size_t)(es.n + 1) * sizeof *hits);
	for (int y = 0; y < im->h; y++) {
		memset(row, 0, (size_t)(im->w + 2) * sizeof *row);
		bool any = false;
		for (int sub = 0; sub < SUB; sub++) {
			double sy = y + (sub + 0.5) / SUB;
			int nh = 0;
			for (int k = 0; k < es.n; k++) {
				Edge *e = &es.e[k];
				if (sy < e->y0 || sy >= e->y1)
					continue;
				double t = (sy - e->y0) / (e->y1 - e->y0);
				hits[nh++] = (Hit){e->x0 + (e->x1 - e->x0) * t, e->dir};
			}
			qsort(hits, (size_t)nh, sizeof *hits, hit_cmp);
			int wind = 0;
			for (int k = 0; k + 1 < nh; k++) {
				wind += hits[k].dir;
				if (!wind)
					continue;
				double a = fmax(hits[k].x, 0), b = fmin(hits[k + 1].x, im->w);
				if (b <= a)
					continue;
				any = true;
				int ia = (int)a, ib = (int)b;
				if (ia == ib) {
					row[ia] += (float)((b - a) / SUB);
					continue;
				}
				row[ia] += (float)((ia + 1 - a) / SUB);
				for (int x = ia + 1; x < ib; x++)
					row[x] += 1.0f / SUB;
				if (ib < im->w)
					row[ib] += (float)((b - ib) / SUB);
			}
		}
		if (!any)
			continue;
		for (int x = 0; x < im->w; x++) {
			float v = row[x] > 1 ? 1 : row[x];
			int q = im->px[(long)y * im->w + x] + (int)lroundf(v * 255);
			im->px[(long)y * im->w + x] = (uint8_t)(q > 255 ? 255 : q);
		}
	}
	free(row);
	free(hits);
	free(es.e);
}
