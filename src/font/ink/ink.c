#include "font/ink/ink.h"
#include "font/ink/stamp.h"
#include "base/mem.h"

#include <math.h>
#include <stdlib.h>

void ink_init(Ink *k)
{
	k->s = NULL;
	k->n = k->cap = 0;
}

void ink_free(Ink *k)
{
	for (int i = 0; i < k->n; i++)
		poly_free(&k->s[i].line);
	free(k->s);
	ink_init(k);
}

static Shape *add(Ink *k)
{
	XGROW(k->s, k->cap, k->n + 1);
	Shape *s = &k->s[k->n++];
	*s = (Shape){0};
	poly_init(&s->line);
	return s;
}

void ink_stroke(Ink *k, const Poly *line, double width, Cap c0, Cap c1)
{
	if (line->n < 2)
		return;
	Shape *s = add(k);
	s->kind = SHAPE_STROKE;
	poly_copy(&s->line, line);
	s->r = width / 2;
	s->c0 = c0;
	s->c1 = c1;
}

void ink_loop(Ink *k, const Poly *line, double width)
{
	if (line->n < 3)
		return;
	Shape *s = add(k);
	s->kind = SHAPE_STROKE;
	poly_copy(&s->line, line);
	s->closed = true;
	s->r = width / 2;
	s->c0 = s->c1 = CAP_ROUND;
}

void ink_disc(Ink *k, Vec2 c, double r)
{
	Shape *s = add(k);
	s->kind = SHAPE_DISC;
	s->c = c;
	s->r = r;
}

bool ink_bbox(const Ink *k, double box[4])
{
	box[0] = box[1] = INFINITY;
	box[2] = box[3] = -INFINITY;
	for (int i = 0; i < k->n; i++) {
		const Shape *s = &k->s[i];
		if (s->kind == SHAPE_DISC) {
			box[0] = fmin(box[0], s->c.x - s->r);
			box[1] = fmin(box[1], s->c.y - s->r);
			box[2] = fmax(box[2], s->c.x + s->r);
			box[3] = fmax(box[3], s->c.y + s->r);
			continue;
		}
		for (int j = 0; j < s->line.n; j++) {
			Vec2 p = s->line.p[j];
			box[0] = fmin(box[0], p.x - s->r);
			box[1] = fmin(box[1], p.y - s->r);
			box[2] = fmax(box[2], p.x + s->r);
			box[3] = fmax(box[3], p.y + s->r);
		}
	}
	return k->n > 0;
}

void ink_render(const Ink *k, Field *f)
{
	for (int i = 0; i < k->n; i++) {
		const Shape *s = &k->s[i];
		if (s->kind == SHAPE_DISC)
			stamp_disc(f, s->c, s->r);
		else
			stamp_stroke(f, s->line.p, s->line.n, s->closed, s->r,
				     s->c0, s->c1);
	}
}
