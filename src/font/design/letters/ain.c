#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define C_RX 128.0     /* the open c of the initial and isolated forms */
#define C_RY 140.0
#define C_OPEN 38.0    /* angle of the c's upper terminal */
#define HEART_W 300.0  /* the closed head of the medial and final forms */
#define HEART_H 330.0
#define BOWL_W 400.0

/* the big lower bowl, opening right, entered at (x, y) */
static void bowl(Pen *p, double x, double y)
{
	double w = p->bw;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x, y, 0,
	      HS, -70, 150,
	      HS, DEEP + HS, BOWL_R,
	      w - HS + 10, DEEP + HS, 0);
}

/* a c opening right whose bottom lands at (cx, BY) */
static void open_c(Pen *p, double cx, double bottom)
{
	double cy = bottom + C_RY;
	pen_move(p, cx + C_RX * 0.79, cy + C_RY * 0.62);
	pen_arc(p, cx, cy, C_RX, C_RY, C_OPEN, 270);
}

/* a head like an upturned teardrop standing on its point at (cx, BY) */
static void heart(Pen *p, double cx)
{
	double t = HEART_H - HS, hw = HEART_W / 2 - HS;
	RPATH_LOOP(p,
		   cx, BY, 0,
		   cx - hw, t - 60, 120,
		   cx - hw * 0.55, t, 90,
		   cx + hw * 0.55, t, 90,
		   cx + hw, t - 60, 120);
}

void body_ain(Pen *p, Form f)
{
	if (f == FORM_INIT) {
		p->bw = 2 * C_RX + ST + 10;
		double cx = HS + C_RX + 10;
		open_c(p, cx, BY);
		pen_line(p, 0, BY);
		pen_stroke(p, CAP_FLAT, CAP_FLAT);
		pen_anchor_above(p, cx, BY + 2 * C_RY + HS + DOT_CLEAR);
		pen_anchor_below(p, cx, -DOT_CLEAR);
		return;
	}
	if (f == FORM_MEDI) {
		p->bw = HEART_W + 40;
		double cx = p->bw / 2;
		heart(p, cx);
		part_baseline(p, 0, p->bw);
		pen_anchor_above(p, cx, HEART_H + DOT_CLEAR);
		pen_anchor_below(p, cx, -DOT_CLEAR);
		return;
	}
	p->bw = BOWL_W;
	double cx = p->bw * 0.55;
	if (f == FORM_FINA) {
		heart(p, cx);
		part_baseline(p, cx, p->bw);
		bowl(p, cx, BY);
		pen_anchor_above(p, cx, HEART_H + DOT_CLEAR);
	} else {
		/* the c meets the bowl at a point on its way down */
		double jy = 70;
		open_c(p, cx - 20, jy);
		pen_stroke(p, CAP_FLAT, CAP_FLAT);
		bowl(p, cx - 20, jy);
		pen_anchor_above(p, cx - 20, jy + 2 * C_RY + HS + DOT_CLEAR);
	}
	pen_anchor_below(p, cx, DEEP - DOT_CLEAR);
}
