#include "font/design/symbols/symbol.h"
#include "font/design/style.h"

#include <math.h>

#define PR 48.0        /* period dot radius */
#define CAPH 720.0
#define MATH_Y 330.0   /* center line for dashes and math signs */

static void dot(Pen *p, double x, double y) { pen_disc(p, x, y, PR); }

static void period(Pen *p)
{
	p->bw = 2 * PR;
	dot(p, PR, PR);
}

static void colon(Pen *p)
{
	p->bw = 2 * PR;
	dot(p, PR, PR);
	dot(p, PR, 380);
}

/* latin comma: a slanted wedge hanging below the baseline */
static void comma_at(Pen *p, double x, double y)
{
	pen_segment(p, x + 26, y + 90, x - 20, y - 120);
}

static void comma(Pen *p)
{
	p->bw = 90;
	comma_at(p, 55, 0);
}

static void semicolon(Pen *p)
{
	p->bw = 2 * PR;
	comma_at(p, PR + 5, 0);
	dot(p, PR, 380);
}

/* arabic comma: the latin one turned over, sitting on the baseline */
static void ar_comma_at(Pen *p, double x, double y)
{
	pen_segment(p, x - 26, y, x + 20, y + 210);
}

static void ar_comma(Pen *p)
{
	p->bw = 90;
	ar_comma_at(p, 35, 0);
}

static void ar_semicolon(Pen *p)
{
	p->bw = 2 * PR;
	ar_comma_at(p, PR - 5, 260);
	dot(p, PR, PR);
}

static void exclam(Pen *p)
{
	p->bw = 2 * PR;
	pen_segment(p, PR, 210, PR, CAPH);
	dot(p, PR, PR);
}

static void question_shape(Pen *p, double flip)
{
	double c = 180, x = flip > 0 ? 0 : 360;
	p->bw = 360;
	pen_move(p, x + flip * (c - 150), 545);
	pen_arc(p, x + flip * c, 540, 150, 140, flip > 0 ? 175 : 5, flip > 0 ? -70 : 250);
	pen_line(p, x + flip * c, 330);
	pen_line(p, x + flip * c, 220);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
	dot(p, x + flip * c, PR);
}

static void question(Pen *p) { question_shape(p, 1); }
static void ar_question(Pen *p) { question_shape(p, -1); }

static void quotedbl(Pen *p)
{
	p->bw = 190;
	pen_segment(p, HS, CAPH, HS, 500);
	pen_segment(p, 190 - HS, CAPH, 190 - HS, 500);
}

static void quotesingle(Pen *p)
{
	p->bw = ST;
	pen_segment(p, HS, CAPH, HS, 500);
}

static void paren(Pen *p, double flip)
{
	double x0 = flip > 0 ? 0 : 200;
	p->bw = 200;
	pen_move(p, x0 + flip * 190, 800);
	pen_cubic(p, x0 + flip * 40, 620, x0 + flip * 40, 0, x0 + flip * 190, -180);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void parenleft(Pen *p) { paren(p, 1); }
static void parenright(Pen *p) { paren(p, -1); }

static void bracket(Pen *p, double flip)
{
	double x0 = flip > 0 ? 0 : 200;
	p->bw = 200;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x0 + flip * 200, 800 - HS, 0,
	      x0 + flip * HS, 800 - HS, 0,
	      x0 + flip * HS, -180 + HS, 0,
	      x0 + flip * 200, -180 + HS, 0);
}

static void bracketleft(Pen *p) { bracket(p, 1); }
static void bracketright(Pen *p) { bracket(p, -1); }

static void hyphen(Pen *p)
{
	p->bw = 260;
	pen_segment(p, 0, MATH_Y, 260, MATH_Y);
}

static void endash(Pen *p)
{
	p->bw = 500;
	pen_segment(p, 0, MATH_Y, 500, MATH_Y);
}

static void emdash(Pen *p)
{
	p->bw = 1000;
	pen_segment(p, 0, MATH_Y, 1000, MATH_Y);
}

static void slash(Pen *p)
{
	p->bw = 300;
	pen_segment(p, 20, -120, 280, CAPH + 40);
}

static void backslash(Pen *p)
{
	p->bw = 300;
	pen_segment(p, 280, -120, 20, CAPH + 40);
}

static void percent(Pen *p)
{
	p->bw = 640;
	pen_ring(p, 130, 570, 95, 110);
	pen_ring(p, 510, 150, 95, 110);
	pen_segment(p, 90, 0, 550, CAPH);
}

static void ar_percent(Pen *p)
{
	p->bw = 420;
	pen_segment(p, 70, 20, 350, 640);
	pen_disc(p, 110, 540, DOT_R);
	pen_disc(p, 310, 110, DOT_R);
}

static void plus(Pen *p)
{
	p->bw = 460;
	pen_segment(p, 0, MATH_Y, 460, MATH_Y);
	pen_segment(p, 230, MATH_Y - 230, 230, MATH_Y + 230);
}

static void minus(Pen *p)
{
	p->bw = 460;
	pen_segment(p, 0, MATH_Y, 460, MATH_Y);
}

static void equal(Pen *p)
{
	p->bw = 460;
	pen_segment(p, 0, MATH_Y + 95, 460, MATH_Y + 95);
	pen_segment(p, 0, MATH_Y - 95, 460, MATH_Y - 95);
}

static void multiply(Pen *p)
{
	p->bw = 400;
	pen_segment(p, 30, MATH_Y - 170, 370, MATH_Y + 170);
	pen_segment(p, 30, MATH_Y + 170, 370, MATH_Y - 170);
}

static void asterisk(Pen *p)
{
	p->bw = 360;
	double cy = 560, r = 160;
	for (int i = 0; i < 3; i++) {
		double a = M_PI / 2 + i * M_PI / 3;
		pen_segment(p, 180 + r * cos(a), cy + r * sin(a),
			    180 - r * cos(a), cy - r * sin(a));
	}
}

static void underscore(Pen *p)
{
	p->bw = 500;
	pen_segment(p, 0, -140, 500, -140);
}

static void guillemet(Pen *p, double flip)
{
	p->bw = 420;
	double x0 = flip > 0 ? 20 : 400;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x0 + flip * 150, MATH_Y + 150, 0,
	      x0, MATH_Y, 0,
	      x0 + flip * 150, MATH_Y - 150, 0);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x0 + flip * 340, MATH_Y + 150, 0,
	      x0 + flip * 190, MATH_Y, 0,
	      x0 + flip * 340, MATH_Y - 150, 0);
}

static void guillemetleft(Pen *p) { guillemet(p, 1); }
static void guillemetright(Pen *p) { guillemet(p, -1); }

static void angle(Pen *p, double flip)
{
	p->bw = 420;
	double x0 = flip > 0 ? 20 : 400;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x0 + flip * 380, MATH_Y + 230, 0,
	      x0, MATH_Y, 0,
	      x0 + flip * 380, MATH_Y - 230, 0);
}

static void anglel(Pen *p) { angle(p, 1); }
static void angler(Pen *p) { angle(p, -1); }

static void ellipsis(Pen *p)
{
	p->bw = 2 * PR + 2 * 230;
	for (int i = 0; i < 3; i++)
		dot(p, PR + i * 230, PR);
}

static void numbersign(Pen *p)
{
	p->bw = 560;
	pen_segment(p, 0, 470, 560, 470);
	pen_segment(p, 0, 230, 560, 230);
	pen_segment(p, 170, 0, 230, CAPH);
	pen_segment(p, 350, 0, 410, CAPH);
}

static void ar_decimal(Pen *p)
{
	p->bw = 110;
	pen_segment(p, 40, -60, 75, 140);
}

static void ar_thousands(Pen *p)
{
	p->bw = 110;
	pen_segment(p, 75, 640, 40, 440);
}

static void bullet(Pen *p)
{
	p->bw = 2 * 80;
	pen_disc(p, 80, MATH_Y, 80);
}

static const SymbolDef defs[] = {
	{"period", {'.'}, period, false},
	{"colon", {':'}, colon, false},
	{"comma", {','}, comma, false},
	{"semicolon", {';'}, semicolon, false},
	{"commaarabic", {0x060C}, ar_comma, false},
	{"semicolonarabic", {0x061B}, ar_semicolon, false},
	{"exclam", {'!'}, exclam, false},
	{"question", {'?'}, question, false},
	{"questionarabic", {0x061F}, ar_question, false},
	{"quotedbl", {'"'}, quotedbl, false},
	{"quotesingle", {'\''}, quotesingle, false},
	{"parenleft", {'('}, parenleft, false},
	{"parenright", {')'}, parenright, false},
	{"bracketleft", {'['}, bracketleft, false},
	{"bracketright", {']'}, bracketright, false},
	{"hyphen", {'-'}, hyphen, false},
	{"endash", {0x2013}, endash, false},
	{"emdash", {0x2014}, emdash, true},
	{"slash", {'/'}, slash, false},
	{"backslash", {'\\'}, backslash, false},
	{"percent", {'%'}, percent, false},
	{"percentarabic", {0x066A}, ar_percent, false},
	{"plus", {'+'}, plus, false},
	{"minus", {0x2212}, minus, false},
	{"equal", {'='}, equal, false},
	{"multiply", {0x00D7}, multiply, false},
	{"asterisk", {'*'}, asterisk, false},
	{"underscore", {'_'}, underscore, false},
	{"less", {'<'}, anglel, false},
	{"greater", {'>'}, angler, false},
	{"guillemetleft", {0x00AB}, guillemetleft, false},
	{"guillemetright", {0x00BB}, guillemetright, false},
	{"ellipsis", {0x2026}, ellipsis, false},
	{"numbersign", {'#'}, numbersign, false},
	{"decimalarabic", {0x066B}, ar_decimal, false},
	{"thousandsarabic", {0x066C}, ar_thousands, false},
	{"bullet", {0x2022}, bullet, false},
};

const SymbolDef *punct_defs(int *n)
{
	*n = (int)(sizeof defs / sizeof *defs);
	return defs;
}
