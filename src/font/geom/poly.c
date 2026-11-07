#include "font/geom/poly.h"
#include "base/mem.h"

#include <stdlib.h>
#include <string.h>

void poly_init(Poly *pl)
{
	pl->p = NULL;
	pl->n = pl->cap = 0;
}

void poly_free(Poly *pl)
{
	free(pl->p);
	poly_init(pl);
}

void poly_clear(Poly *pl)
{
	pl->n = 0;
}

void poly_push(Poly *pl, Vec2 v)
{
	if (pl->n && v2_dist(pl->p[pl->n - 1], v) < 1e-9)
		return;
	XGROW(pl->p, pl->cap, pl->n + 1);
	pl->p[pl->n++] = v;
}

void poly_copy(Poly *dst, const Poly *src)
{
	poly_init(dst);
	XGROW(dst->p, dst->cap, src->n);
	memcpy(dst->p, src->p, (size_t)src->n * sizeof *src->p);
	dst->n = src->n;
}

Vec2 poly_last(const Poly *pl)
{
	return pl->p[pl->n - 1];
}
