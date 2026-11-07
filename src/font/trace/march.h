#ifndef BFA_FONT_TRACE_MARCH_H
#define BFA_FONT_TRACE_MARCH_H

#include "font/geom/poly.h"
#include "font/ink/field.h"

typedef struct {
	Poly *loop;
	int n, cap;
} Loops;

void loops_free(Loops *l);

/* marching squares over the zero level. every loop keeps the ink on its
   right, so outer loops run clockwise and holes counter-clockwise. */
void march(const Field *f, Loops *out);

#endif
