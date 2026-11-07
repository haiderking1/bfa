#ifndef BFA_FONT_DESIGN_LETTER_H
#define BFA_FONT_DESIGN_LETTER_H

#include "font/design/pen.h"
#include "font/shape/joining.h"

typedef void (*BodyFn)(Pen *p, Form f);

typedef enum {
	MARK_NONE,
	MARK_HAMZA_ABOVE,
	MARK_HAMZA_BELOW,
	MARK_MADDA,
} ExtraMark;

typedef struct {
	int above, below; /* dot counts */
	ExtraMark extra;
	int joined_below; /* dots below on init/medi when they differ, else -1 */
} MarkSpec;

typedef struct {
	uint32_t cp;
	BodyFn body;
	MarkSpec marks;
} LetterDef;

const LetterDef *letter_defs(int *n);
const LetterDef *letter_def(uint32_t cp);

#endif
