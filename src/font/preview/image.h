#ifndef BFA_FONT_PREVIEW_IMAGE_H
#define BFA_FONT_PREVIEW_IMAGE_H

#include <stdint.h>

/* 8-bit coverage image, 0 = paper, 255 = full ink */
typedef struct {
	int w, h;
	uint8_t *px;
} Image;

void image_init(Image *im, int w, int h);
void image_free(Image *im);
void image_hline(Image *im, int y, int x0, int x1, uint8_t v);
void image_vline(Image *im, int x, int y0, int y1, uint8_t v);

#endif
