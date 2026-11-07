#ifndef BFA_FONT_DESIGN_PARTS_H
#define BFA_FONT_DESIGN_PARTS_H

#include "font/design/pen.h"

/* n dots (1..3) whose group edge nearest the letter sits at (x, y) */
void part_dots(Pen *p, int n, double x, double y, bool above);

/* hamza drawn into a box of the given height, bottom center at (x, y) */
void part_hamza(Pen *p, double x, double y, double height);
#define HAMZA_MARK_H 170.0
#define HAMZA_FULL_H 330.0

/* the wave over alef madda, bottom center at (x, y) */
void part_madda(Pen *p, double x, double y);
#define MADDA_H 90.0

/* baseline run at BY between x0 and x1 */
void part_baseline(Pen *p, double x0, double x1);

#endif
