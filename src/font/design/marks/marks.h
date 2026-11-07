#ifndef BFA_FONT_DESIGN_MARKS_MARKS_H
#define BFA_FONT_DESIGN_MARKS_MARKS_H

#include "font/design/pen.h"
#include "font/glyph/glyph.h"

#include <stdint.h>

/* marks are drawn around x = 0 hanging off their attach point: above
   marks grow up from MARK_ABOVE_Y, below marks grow down from MARK_BELOW_Y */
#define MARK_ABOVE_Y 600.0
#define MARK_BELOW_Y -160.0

typedef struct {
	const char *name;
	uint32_t cp;
	MarkSide side;
	void (*draw)(Pen *p, double y); /* y: the attach line */
} MarkDef;

const MarkDef *mark_defs(int *n);

#endif
