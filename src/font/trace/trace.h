#ifndef BFA_FONT_TRACE_TRACE_H
#define BFA_FONT_TRACE_TRACE_H

#include "font/ink/ink.h"
#include "font/outline/outline.h"

/* rasterize the ink's distance field at step units and fit the outline */
void trace_ink(const Ink *k, double step, double tol, Outline *out);

#endif
