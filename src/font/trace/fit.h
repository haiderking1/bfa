#ifndef BFA_FONT_TRACE_FIT_H
#define BFA_FONT_TRACE_FIT_H

#include "font/geom/poly.h"
#include "font/outline/outline.h"

/* turn a dense traced loop into lines and quadratic curves within tol font
   units, keeping sharp corners sharp */
void fit_loop(const Poly *loop, double tol, Outline *out);

#endif
