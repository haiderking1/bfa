#include "font/trace/march.h"
#include "base/mem.h"

#include <stdlib.h>

void loops_free(Loops *l)
{
	for (int i = 0; i < l->n; i++)
		poly_free(&l->loop[i]);
	free(l->loop);
	l->loop = NULL;
	l->n = l->cap = 0;
}

typedef struct {
	const Field *f;
	long nh; /* count of horizontal edges */
} Grid;

static float val(const Field *f, int i, int j)
{
	return f->d[(long)j * f->nx + i];
}

static int inside(const Field *f, int i, int j)
{
	return val(f, i, j) < 0;
}

/* edge ids: bottom of cell (i,j) is horizontal (i,j), left is vertical (i,j) */
static long hedge(const Grid *g, int i, int j)
{
	return (long)j * (g->f->nx - 1) + i;
}

static long vedge(const Grid *g, int i, int j)
{
	return g->nh + (long)j * g->f->nx + i;
}

static Vec2 cross_point(const Grid *g, long e)
{
	const Field *f = g->f;
	int i0, j0, i1, j1;
	if (e < g->nh) {
		j0 = (int)(e / (f->nx - 1));
		i0 = (int)(e % (f->nx - 1));
		i1 = i0 + 1;
		j1 = j0;
	} else {
		long v = e - g->nh;
		j0 = (int)(v / f->nx);
		i0 = (int)(v % f->nx);
		i1 = i0;
		j1 = j0 + 1;
	}
	double a = val(f, i0, j0), b = val(f, i1, j1);
	double t = a / (a - b);
	double x = i0 + (i1 - i0) * t, y = j0 + (j1 - j0) * t;
	return v2(f->x0 + x * f->step, f->y0 + y * f->step);
}

void march(const Field *f, Loops *out)
{
	Grid g = {f, (long)f->ny * (f->nx - 1)};
	long ne = g.nh + (long)(f->ny - 1) * f->nx;
	long *next = xmalloc((size_t)ne * sizeof *next);
	for (long e = 0; e < ne; e++)
		next[e] = -1;

	for (int j = 0; j + 1 < f->ny; j++)
		for (int i = 0; i + 1 < f->nx; i++) {
			int b[4] = {inside(f, i, j), inside(f, i + 1, j),
				    inside(f, i + 1, j + 1), inside(f, i, j + 1)};
			/* edges in ccw order: bottom, right, top, left */
			long e[4] = {hedge(&g, i, j), vedge(&g, i + 1, j),
				     hedge(&g, i, j + 1), vedge(&g, i, j)};
			int entry[2], exit_[2], ne_ = 0, nx_ = 0;
			for (int k = 0; k < 4; k++) {
				int a = b[k], c = b[(k + 1) & 3];
				if (!a && c)
					entry[ne_++] = k;
				else if (a && !c)
					exit_[nx_++] = k;
			}
			if (ne_ == 1) {
				next[e[entry[0]]] = e[exit_[0]];
			} else if (ne_ == 2) {
				double ctr = (val(f, i, j) + val(f, i + 1, j) +
					      val(f, i + 1, j + 1) + val(f, i, j + 1)) / 4;
				/* entry k pairs with the exit just after it when the
				   inside corners are separate, before it when joined */
				for (int q = 0; q < 2; q++) {
					int k = entry[q];
					int x = ctr < 0 ? (k + 3) & 3 : (k + 1) & 3;
					next[e[k]] = e[x];
				}
			}
		}

	for (long s = 0; s < ne; s++) {
		if (next[s] < 0)
			continue;
		XGROW(out->loop, out->cap, out->n + 1);
		Poly *pl = &out->loop[out->n++];
		poly_init(pl);
		long e = s;
		while (next[e] >= 0) {
			poly_push(pl, cross_point(&g, e));
			long nx = next[e];
			next[e] = -1;
			e = nx;
		}
		if (pl->n < 3) {
			poly_free(pl);
			out->n--;
		}
	}
	free(next);
}
