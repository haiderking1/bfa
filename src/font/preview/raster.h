#ifndef BFA_FONT_PREVIEW_RASTER_H
#define BFA_FONT_PREVIEW_RASTER_H

#include "font/outline/outline.h"
#include "font/preview/image.h"

/* fill an outline (nonzero) into im. font (x,y) lands on pixel
   (ox + x*scale, oy - y*scale). */
void raster_outline(Image *im, const Outline *o, double scale, double ox,
		    double oy);

#endif
