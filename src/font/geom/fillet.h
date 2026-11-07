#ifndef BFA_FONT_GEOM_FILLET_H
#define BFA_FONT_GEOM_FILLET_H

#include "font/geom/poly.h"

/* append the polyline v[0..n) to out with every interior corner rounded:
   by radii[i] when radii is given, else by r (shrunk where the legs are too
   short). closed treats v as a loop. */
void fillet(Poly *out, const Vec2 *v, const double *radii, int n, double r,
	    int closed, double tol);

#endif
