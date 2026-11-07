#ifndef BFA_FONT_INK_INK_H
#define BFA_FONT_INK_INK_H

#include "font/geom/poly.h"
#include "font/ink/field.h"

#include <stdbool.h>

typedef enum { CAP_FLAT, CAP_ROUND } Cap;

typedef enum { SHAPE_STROKE, SHAPE_DISC } ShapeKind;

typedef struct {
	ShapeKind kind;
	Poly line;   /* stroke centerline */
	bool closed;
	double r;    /* half width, or disc radius */
	Cap c0, c1;
	Vec2 c;      /* disc center */
} Shape;

/* the ink of one glyph: a union of shapes */
typedef struct {
	Shape *s;
	int n, cap;
} Ink;

void ink_init(Ink *k);
void ink_free(Ink *k);
void ink_stroke(Ink *k, const Poly *line, double width, Cap c0, Cap c1);
void ink_loop(Ink *k, const Poly *line, double width);
void ink_disc(Ink *k, Vec2 c, double r);

/* box = xmin, ymin, xmax, ymax of the inked area. false when empty. */
bool ink_bbox(const Ink *k, double box[4]);

/* write the union's signed distance into f (min with what's there) */
void ink_render(const Ink *k, Field *f);

#endif
