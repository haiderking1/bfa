#ifndef BFA_FONT_DESIGN_PEN_H
#define BFA_FONT_DESIGN_PEN_H

#include "font/geom/poly.h"
#include "font/ink/ink.h"

/* where a letter wants its dots and marks, in body coords */
typedef struct {
	Vec2 above, below;
	bool has_above, has_below;
} Anchors;

typedef struct {
	Ink ink;
	Poly path;
	double ox, oy;   /* body origin inside the glyph */
	double sx, sy;   /* scale, for marks drawn at a smaller size */
	double width;    /* stroke width in use */
	double bw;       /* body width, set by the letter */
	Anchors an;
} Pen;

void pen_init(Pen *p);
void pen_free(Pen *p);

/* path building, coordinates in body space */
void pen_move(Pen *p, double x, double y);
void pen_line(Pen *p, double x, double y);
void pen_quad(Pen *p, double cx, double cy, double x, double y);
void pen_cubic(Pen *p, double c1x, double c1y, double c2x, double c2y,
	       double x, double y);
/* elliptical arc around (cx,cy), angles in degrees, ccw positive */
void pen_arc(Pen *p, double cx, double cy, double rx, double ry, double a0,
	     double a1);
void pen_stroke(Pen *p, Cap c0, Cap c1);
void pen_close(Pen *p);

/* rounded polyline through n points given as x,y pairs */
void pen_rpoly(Pen *p, double r, Cap c0, Cap c1, int n, const double *xy);
void pen_rloop(Pen *p, double r, int n, const double *xy);
#define RPOLY(p, r, c0, c1, ...)                                               \
	pen_rpoly(p, r, c0, c1,                                                \
		  (int)(sizeof((double[]){__VA_ARGS__}) / sizeof(double) / 2), \
		  (double[]){__VA_ARGS__})
#define RLOOP(p, r, ...)                                                       \
	pen_rloop(p, r,                                                        \
		  (int)(sizeof((double[]){__VA_ARGS__}) / sizeof(double) / 2), \
		  (double[]){__VA_ARGS__})

/* polyline with a radius per corner: n triples of x, y, r */
void pen_rpath(Pen *p, Cap c0, Cap c1, int n, const double *xyr);
void pen_rpath_loop(Pen *p, int n, const double *xyr);
#define RPATH(p, c0, c1, ...)                                                  \
	pen_rpath(p, c0, c1,                                                   \
		  (int)(sizeof((double[]){__VA_ARGS__}) / sizeof(double) / 3), \
		  (double[]){__VA_ARGS__})
#define RPATH_LOOP(p, ...)                                                     \
	pen_rpath_loop(p,                                                      \
		       (int)(sizeof((double[]){__VA_ARGS__}) / sizeof(double) / 3), \
		       (double[]){__VA_ARGS__})

void pen_segment(Pen *p, double x0, double y0, double x1, double y1);
void pen_disc(Pen *p, double x, double y, double r);
/* a closed elliptical ring with its centerline at rx,ry */
void pen_ring(Pen *p, double cx, double cy, double rx, double ry);

void pen_anchor_above(Pen *p, double x, double y);
void pen_anchor_below(Pen *p, double x, double y);

#endif
