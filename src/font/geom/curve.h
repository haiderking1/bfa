#ifndef BFA_FONT_GEOM_CURVE_H
#define BFA_FONT_GEOM_CURVE_H

#include "font/geom/poly.h"

/* flatteners append points after the start point (which the caller owns) */
void curve_quad(Poly *out, Vec2 p0, Vec2 c, Vec2 p1, double tol);
void curve_cubic(Poly *out, Vec2 p0, Vec2 c1, Vec2 c2, Vec2 p1, double tol);

/* elliptical arc from angle a0 to a1 (radians, ccw positive), appends every
   point including the start */
void curve_arc(Poly *out, Vec2 center, double rx, double ry, double a0,
	       double a1, double tol);

#endif
