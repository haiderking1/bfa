#ifndef BFA_FONT_DESIGN_LETTERS_LOOP_H
#define BFA_FONT_DESIGN_LETTERS_LOOP_H

#include "font/design/pen.h"

/* a closed flat loop resting on the baseline, outer edges x0..x1 and
   0..top. r rounds its corners (clamped to a stadium). */
void loop_flat(Pen *p, double x0, double x1, double top, double r);

#endif
