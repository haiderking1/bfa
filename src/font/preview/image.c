#include "font/preview/image.h"
#include "base/mem.h"

#include <stdlib.h>

void image_init(Image *im, int w, int h)
{
	im->w = w;
	im->h = h;
	im->px = xcalloc((size_t)w * h, 1);
}

void image_free(Image *im)
{
	free(im->px);
	im->px = NULL;
}

void image_hline(Image *im, int y, int x0, int x1, uint8_t v)
{
	if (y < 0 || y >= im->h)
		return;
	for (int x = x0 < 0 ? 0 : x0; x <= x1 && x < im->w; x++)
		if (im->px[(long)y * im->w + x] < v)
			im->px[(long)y * im->w + x] = v;
}

void image_vline(Image *im, int x, int y0, int y1, uint8_t v)
{
	if (x < 0 || x >= im->w)
		return;
	for (int y = y0 < 0 ? 0 : y0; y <= y1 && y < im->h; y++)
		if (im->px[(long)y * im->w + x] < v)
			im->px[(long)y * im->w + x] = v;
}
