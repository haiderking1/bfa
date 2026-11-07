#ifndef BFA_FONT_OUTLINE_OUTLINE_H
#define BFA_FONT_OUTLINE_OUTLINE_H

#include <stdbool.h>

/* truetype style contours: on-curve points and quadratic off-curve points */
typedef struct {
	int x, y;
	bool on;
} OPt;

typedef struct {
	OPt *p;
	int n, cap;
} OContour;

typedef struct {
	OContour *c;
	int n, cap;
} Outline;

typedef struct {
	int xmin, ymin, xmax, ymax;
} Box;

void outline_init(Outline *o);
void outline_free(Outline *o);
OContour *outline_add(Outline *o);
void contour_push(OContour *c, int x, int y, bool on);

int outline_points(const Outline *o);
bool outline_box(const Outline *o, Box *b);
void outline_shift(Outline *o, int dx, int dy);
void outline_append(Outline *dst, const Outline *src);

#endif
