#include "font/design/letters/letters.h"
#include "font/design/form.h"
#include "font/design/style.h"

#define YEH_W 500.0
#define HEAD_H 250.0   /* top of the isolated form's head */
#define LIP 110.0      /* where the bowl's tail ends on the left */

#define CURL_R 75.0
#define FOOT_R 110.0

/* from the right wall at height y, a smooth fall into a flat bottom that
   runs left and turns up into the tail */
static void sweep(Pen *p, double x, double y)
{
	double w = p->bw, bot = DESC + HS;
	pen_cubic(p, x, y - 120, x - 60, bot, w * 0.45, bot);
	pen_line(p, HS + FOOT_R, bot);
	pen_arc(p, HS + FOOT_R, bot + FOOT_R, FOOT_R, FOOT_R, 270, 180);
	pen_line(p, HS, LIP);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

void body_yeh(Pen *p, Form f)
{
	if (joins_left(f)) {
		body_tooth(p, f);
		return;
	}
	p->bw = YEH_W;
	double w = p->bw, x = w - HS;
	if (f == FORM_FINA) {
		pen_move(p, w, BY);
		pen_line(p, x - 30, BY);
		sweep(p, x - 30, BY);
	} else {
		/* a head curling right before the fall */
		double ht = HEAD_H - HS;
		pen_move(p, w * 0.6, ht);
		pen_line(p, x - CURL_R, ht);
		pen_arc(p, x - CURL_R, ht - CURL_R, CURL_R, CURL_R, 90, 0);
		pen_line(p, x, ht - CURL_R - 10);
		sweep(p, x, ht - CURL_R - 10);
	}
	pen_anchor_below(p, w * 0.42, DESC - DOT_CLEAR);
	pen_anchor_above(p, w * 0.62, HEAD_H + DOT_CLEAR);
}
