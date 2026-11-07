#ifndef BFA_FONT_GEOM_POLY_H
#define BFA_FONT_GEOM_POLY_H

#include "base/vec.h"

/* a flattened polyline */
typedef struct {
	Vec2 *p;
	int n, cap;
} Poly;

void poly_init(Poly *pl);
void poly_free(Poly *pl);
void poly_clear(Poly *pl);
void poly_push(Poly *pl, Vec2 v);
void poly_copy(Poly *dst, const Poly *src);
Vec2 poly_last(const Poly *pl);

#endif
