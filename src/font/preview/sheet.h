#ifndef BFA_FONT_PREVIEW_SHEET_H
#define BFA_FONT_PREVIEW_SHEET_H

#include "font/glyph/font.h"

/* every glyph in a grid with its baseline and advance marked */
int sheet_write(const Font *f, const char *path, int cols, double em_px);

#endif
