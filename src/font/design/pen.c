#include "font/design/pen.h"
#include "font/design/style.h"
#include "font/geom/curve.h"
#include "font/geom/fillet.h"

#include <math.h>
#include <stddef.h>

void pen_init(Pen *p)
{
	ink_init(&p->ink);
	poly_init(&p->path);
	p->ox = p->oy = 0;
	p->sx = p->sy = 1;
	p->width = ST;
	p->bw = 0;
	p->an = (Anchors){{0, 0}, {0, 0}, false, false};
}

void pen_free(Pen *p)
{
	ink_free(&p->ink);
	poly_free(&p->path);
}

static Vec2 xf(const Pen *p, double x, double y)
{
	return v2(p->ox + x * p->sx, p->oy + y * p->sy);
}

void pen_move(Pen *p, double x, double y)
{
	poly_clear(&p->path);
	poly_push(&p->path, xf(p, x, y));
}

void pen_line(Pen *p, double x, double y)
{
	poly_push(&p->path, xf(p, x, y));
}

void pen_quad(Pen *p, double cx, double cy, double x, double y)
{
	curve_quad(&p->path, poly_last(&p->path), xf(p, cx, cy), xf(p, x, y),
		   FLAT_TOL);
}

void pen_cubic(Pen *p, double c1x, double c1y, double c2x, double c2y,
	       double x, double y)
{
	curve_cubic(&p->path, poly_last(&p->path), xf(p, c1x, c1y),
		    xf(p, c2x, c2y), xf(p, x, y), FLAT_TOL);
}

void pen_arc(Pen *p, double cx, double cy, double rx, double ry, double a0,
	     double a1)
{
	curve_arc(&p->path, xf(p, cx, cy), rx * fabs(p->sx), ry * fabs(p->sy),
		  a0 * M_PI / 180, a1 * M_PI / 180, FLAT_TOL);
}

void pen_stroke(Pen *p, Cap c0, Cap c1)
{
	ink_stroke(&p->ink, &p->path, p->width, c0, c1);
	poly_clear(&p->path);
}

void pen_close(Pen *p)
{
	ink_loop(&p->ink, &p->path, p->width);
	poly_clear(&p->path);
}

#define MAX_VERTS 64

static void rpath(Pen *p, double r, int n, const double *xy, int closed)
{
	Vec2 v[MAX_VERTS];
	if (n > MAX_VERTS)
		n = MAX_VERTS;
	for (int i = 0; i < n; i++)
		v[i] = xf(p, xy[2 * i], xy[2 * i + 1]);
	poly_clear(&p->path);
	fillet(&p->path, v, NULL, n, r * fabs(p->sx), closed, FLAT_TOL);
}

static void rpath3(Pen *p, int n, const double *xyr, int closed)
{
	Vec2 v[MAX_VERTS];
	double rad[MAX_VERTS];
	if (n > MAX_VERTS)
		n = MAX_VERTS;
	for (int i = 0; i < n; i++) {
		v[i] = xf(p, xyr[3 * i], xyr[3 * i + 1]);
		rad[i] = xyr[3 * i + 2] * fabs(p->sx);
	}
	poly_clear(&p->path);
	fillet(&p->path, v, rad, n, 0, closed, FLAT_TOL);
}

void pen_rpath(Pen *p, Cap c0, Cap c1, int n, const double *xyr)
{
	rpath3(p, n, xyr, 0);
	pen_stroke(p, c0, c1);
}

void pen_rpath_loop(Pen *p, int n, const double *xyr)
{
	rpath3(p, n, xyr, 1);
	pen_close(p);
}

void pen_rpoly(Pen *p, double r, Cap c0, Cap c1, int n, const double *xy)
{
	rpath(p, r, n, xy, 0);
	pen_stroke(p, c0, c1);
}

void pen_rloop(Pen *p, double r, int n, const double *xy)
{
	rpath(p, r, n, xy, 1);
	pen_close(p);
}

void pen_segment(Pen *p, double x0, double y0, double x1, double y1)
{
	pen_move(p, x0, y0);
	pen_line(p, x1, y1);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

void pen_disc(Pen *p, double x, double y, double r)
{
	ink_disc(&p->ink, xf(p, x, y), r * fabs(p->sx));
}

void pen_ring(Pen *p, double cx, double cy, double rx, double ry)
{
	poly_clear(&p->path);
	curve_arc(&p->path, xf(p, cx, cy), rx * fabs(p->sx), ry * fabs(p->sy),
		  0, 2 * M_PI, FLAT_TOL);
	p->path.n--; /* the arc repeats its start point */
	pen_close(p);
}

void pen_anchor_above(Pen *p, double x, double y)
{
	p->an.above = v2(x, y);
	p->an.has_above = true;
}

void pen_anchor_below(Pen *p, double x, double y)
{
	p->an.below = v2(x, y);
	p->an.has_below = true;
}
