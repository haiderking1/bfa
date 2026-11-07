#include "font/outline/outline.h"
#include "base/mem.h"

#include <limits.h>
#include <stdlib.h>

void outline_init(Outline *o)
{
	o->c = NULL;
	o->n = o->cap = 0;
}

void outline_free(Outline *o)
{
	for (int i = 0; i < o->n; i++)
		free(o->c[i].p);
	free(o->c);
	outline_init(o);
}

OContour *outline_add(Outline *o)
{
	XGROW(o->c, o->cap, o->n + 1);
	OContour *c = &o->c[o->n++];
	c->p = NULL;
	c->n = c->cap = 0;
	return c;
}

void contour_push(OContour *c, int x, int y, bool on)
{
	if (c->n && c->p[c->n - 1].x == x && c->p[c->n - 1].y == y &&
	    c->p[c->n - 1].on == on)
		return;
	XGROW(c->p, c->cap, c->n + 1);
	c->p[c->n++] = (OPt){x, y, on};
}

int outline_points(const Outline *o)
{
	int n = 0;
	for (int i = 0; i < o->n; i++)
		n += o->c[i].n;
	return n;
}

bool outline_box(const Outline *o, Box *b)
{
	*b = (Box){INT_MAX, INT_MAX, INT_MIN, INT_MIN};
	for (int i = 0; i < o->n; i++)
		for (int k = 0; k < o->c[i].n; k++) {
			OPt p = o->c[i].p[k];
			if (p.x < b->xmin) b->xmin = p.x;
			if (p.y < b->ymin) b->ymin = p.y;
			if (p.x > b->xmax) b->xmax = p.x;
			if (p.y > b->ymax) b->ymax = p.y;
		}
	if (b->xmin > b->xmax) {
		*b = (Box){0, 0, 0, 0};
		return false;
	}
	return true;
}

void outline_shift(Outline *o, int dx, int dy)
{
	for (int i = 0; i < o->n; i++)
		for (int k = 0; k < o->c[i].n; k++) {
			o->c[i].p[k].x += dx;
			o->c[i].p[k].y += dy;
		}
}

void outline_append(Outline *dst, const Outline *src)
{
	for (int i = 0; i < src->n; i++) {
		OContour *c = outline_add(dst);
		for (int k = 0; k < src->c[i].n; k++)
			contour_push(c, src->c[i].p[k].x, src->c[i].p[k].y,
				     src->c[i].p[k].on);
	}
}
