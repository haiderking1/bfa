#ifndef BFA_FONT_INK_STAMP_H
#define BFA_FONT_INK_STAMP_H

#include "font/ink/field.h"
#include "font/ink/ink.h"

void stamp_disc(Field *f, Vec2 c, double r);
void stamp_stroke(Field *f, const Vec2 *p, int n, bool closed, double r,
		  Cap c0, Cap c1);

#endif
