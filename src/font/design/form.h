#ifndef BFA_FONT_DESIGN_FORM_H
#define BFA_FONT_DESIGN_FORM_H

#include "font/shape/joining.h"

#include <stdbool.h>

/* right-to-left: the previous letter sits on the right */
static inline bool joins_left(Form f) { return f == FORM_INIT || f == FORM_MEDI; }
static inline bool joins_right(Form f) { return f == FORM_FINA || f == FORM_MEDI; }

#endif
