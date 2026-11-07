#include "check.h"
#include "outline_util.h"
#include "font/geom/curve.h"
#include "font/trace/trace.h"

#include <math.h>
#include <stdlib.h>

static void disc(void)
{
	Ink k;
	ink_init(&k);
	ink_disc(&k, v2(100, 50), 55);
	Outline o;
	outline_init(&o);
	trace_ink(&k, 1.0, 0.3, &o);
	CHECK_EQ(o.n, 1);
	CHECK(contour_area(&o.c[0]) < 0);
	CHECK(contour_max_radial_err(&o.c[0], 100, 50, 55) < 0.6);
	Box b;
	CHECK(outline_box(&o, &b));
	CHECK(abs(b.xmin - 45) <= 6 && abs(b.xmax - 155) <= 6);
	outline_free(&o);
	ink_free(&k);
}

static void ring(void)
{
	Ink k;
	ink_init(&k);
	Poly p;
	poly_init(&p);
	curve_arc(&p, v2(0, 0), 150, 150, 0, 2 * M_PI, 0.25);
	p.n--;
	ink_loop(&k, &p, 60);
	Outline o;
	outline_init(&o);
	trace_ink(&k, 1.0, 0.3, &o);
	CHECK_EQ(o.n, 2);
	if (o.n == 2) {
		double a0 = contour_area(&o.c[0]), a1 = contour_area(&o.c[1]);
		CHECK(a0 * a1 < 0); /* outer and hole run opposite ways */
		double outer = fabs(a0) > fabs(a1) ? a0 : a1;
		CHECK(outer < 0);
		const OContour *oc = fabs(a0) > fabs(a1) ? &o.c[0] : &o.c[1];
		const OContour *ic = fabs(a0) > fabs(a1) ? &o.c[1] : &o.c[0];
		CHECK(contour_max_radial_err(oc, 0, 0, 180) < 0.7);
		CHECK(contour_max_radial_err(ic, 0, 0, 120) < 0.7);
	}
	outline_free(&o);
	poly_free(&p);
	ink_free(&k);
}

static void flat_caps(void)
{
	/* a flat capped bar is an exact rectangle with 4 corners */
	Ink k;
	ink_init(&k);
	Poly p;
	poly_init(&p);
	poly_push(&p, v2(0, 40));
	poly_push(&p, v2(300, 40));
	ink_stroke(&k, &p, 80, CAP_FLAT, CAP_FLAT);
	Outline o;
	outline_init(&o);
	trace_ink(&k, 1.0, 0.3, &o);
	CHECK_EQ(o.n, 1);
	Box b;
	outline_box(&o, &b);
	CHECK_EQ(b.xmin, 0);
	CHECK_EQ(b.xmax, 300);
	CHECK_EQ(b.ymin, 0);
	CHECK_EQ(b.ymax, 80);
	int on = 0;
	for (int i = 0; i < o.c[0].n; i++)
		on += o.c[0].p[i].on;
	CHECK_EQ(on, o.c[0].n);
	CHECK(o.c[0].n <= 6);
	outline_free(&o);
	poly_free(&p);
	ink_free(&k);
}

static void union_of_overlaps(void)
{
	/* a plus sign made of two bars traces as one outline */
	Ink k;
	ink_init(&k);
	Poly p;
	poly_init(&p);
	poly_push(&p, v2(-200, 0));
	poly_push(&p, v2(200, 0));
	ink_stroke(&k, &p, 60, CAP_FLAT, CAP_FLAT);
	poly_clear(&p);
	poly_push(&p, v2(0, -200));
	poly_push(&p, v2(0, 200));
	ink_stroke(&k, &p, 60, CAP_FLAT, CAP_FLAT);
	Outline o;
	outline_init(&o);
	trace_ink(&k, 1.0, 0.3, &o);
	CHECK_EQ(o.n, 1);
	CHECK(o.n && o.c[0].n >= 12 && o.c[0].n <= 16);
	outline_free(&o);
	poly_free(&p);
	ink_free(&k);
}

int main(void)
{
	disc();
	ring();
	flat_caps();
	union_of_overlaps();
	return CHECK_DONE();
}
