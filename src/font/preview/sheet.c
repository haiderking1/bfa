#include "font/preview/sheet.h"
#include "font/preview/png.h"
#include "font/preview/raster.h"

#include <math.h>

#define GUIDE 40

int sheet_write(const Font *f, const char *path, int cols, double em_px)
{
	double s = em_px / f->info.upm;
	int cell_w = (int)ceil(em_px * 1.1), cell_h = (int)ceil(em_px * 1.8);
	int rows = (f->gs.n + cols - 1) / cols;
	Image im;
	image_init(&im, cols * cell_w, rows * cell_h);
	for (int i = 0; i < f->gs.n; i++) {
		const Glyph *g = &f->gs.g[i];
		int cx = (i % cols) * cell_w, cy = (i / cols) * cell_h;
		double ox = cx + (cell_w - g->adv * s) / 2;
		double base = cy + cell_h * 0.62;
		image_hline(&im, (int)base, cx + 4, cx + cell_w - 4, GUIDE);
		image_vline(&im, (int)ox, cy + 8, cy + cell_h - 8, GUIDE);
		image_vline(&im, (int)(ox + g->adv * s), cy + 8, cy + cell_h - 8, GUIDE);
		raster_outline(&im, &g->ol, s, ox, base);
	}
	int rc = png_write(path, &im);
	image_free(&im);
	return rc;
}
