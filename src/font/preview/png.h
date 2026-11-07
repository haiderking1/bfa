#ifndef BFA_FONT_PREVIEW_PNG_H
#define BFA_FONT_PREVIEW_PNG_H

#include "font/preview/image.h"

/* grayscale png, ink drawn dark on light paper. 0 on success. */
int png_write(const char *path, const Image *im);

#endif
