#ifndef BFA_FONT_DESIGN_SYMBOLS_SYMBOL_H
#define BFA_FONT_DESIGN_SYMBOLS_SYMBOL_H

#include "font/design/pen.h"

#include <stdint.h>

#define SYM_MAX_CP 3

/* a glyph that isn't a joining letter: punctuation, digits, marks */
typedef struct {
	const char *name;
	uint32_t cp[SYM_MAX_CP];
	void (*draw)(Pen *p);
	bool fixed;     /* draw sets the full advance in p->bw, no bearings */
} SymbolDef;

const SymbolDef *punct_defs(int *n);
const SymbolDef *digit_defs(int *n);

#define DIGIT_ADV 580.0

#endif
