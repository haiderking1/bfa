#include "font/design/symbols/symbol.h"
#include "font/design/style.h"

#include <math.h>

/* tabular figures: every digit takes DIGIT_ADV so counters don't wobble */

#define FIG 700.0      /* western figure height */
#define AFIG 640.0     /* arabic-indic figure height */
#define CX (DIGIT_ADV / 2)

static void fixed(Pen *p) { p->bw = DIGIT_ADV; }

static void d0(Pen *p)
{
	fixed(p);
	RLOOP(p, 160, 125, HS, 455, HS, 455, FIG - HS, 125, FIG - HS);
}

static void d1(Pen *p)
{
	fixed(p);
	pen_segment(p, 330, 0, 330, FIG);
	pen_segment(p, 175, 560, 330 + HS * 0.4, FIG - 20);
}

static void d2(Pen *p)
{
	fixed(p);
	pen_move(p, 125, 505);
	pen_arc(p, 290, 500, 165, 165, 178, -32);
	pen_line(p, 130, HS);
	pen_line(p, 470, HS);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void d3(Pen *p)
{
	fixed(p);
	pen_move(p, 135, 560);
	pen_arc(p, 285, 525, 150, 138, 166, -90);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
	pen_move(p, 245, 387);
	pen_arc(p, 285, 205, 175, 182, 90, -158);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void d4(Pen *p)
{
	fixed(p);
	pen_segment(p, 385, 0, 385, FIG);
	pen_move(p, 385, FIG - HS);
	pen_line(p, 95, 220);
	pen_line(p, 500, 220);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void d5(Pen *p)
{
	fixed(p);
	pen_move(p, 455, FIG - HS);
	pen_line(p, 170, FIG - HS);
	pen_line(p, 150, 390);
	pen_arc(p, 290, 235, 180, 180, 128, -150);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void d6(Pen *p)
{
	fixed(p);
	pen_ring(p, CX, 230, 185, 190);
	pen_move(p, 420, FIG - 10);
	pen_cubic(p, 250, FIG - 40, 105, 560, 105, 230);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void d7(Pen *p)
{
	fixed(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      100, FIG - HS, 0,
	      480, FIG - HS, 0,
	      215, 0, 0);
}

static void d8(Pen *p)
{
	fixed(p);
	pen_ring(p, CX, 530, 145, 133);
	pen_ring(p, CX, 205, 178, 168);
}

static void d9(Pen *p)
{
	fixed(p);
	pen_ring(p, CX, 470, 185, 190);
	pen_move(p, 475, 470);
	pen_cubic(p, 475, 140, 330, 10, 160, 10);
	pen_stroke(p, CAP_FLAT, CAP_FLAT);
}

static void a0(Pen *p)
{
	fixed(p);
	/* a small diamond: a square bar turned 45 degrees */
	double c = AFIG * 0.42, d = 38, w = p->width;
	p->width = 2 * M_SQRT2 * d;
	pen_segment(p, CX - d, c - d, CX + d, c + d);
	p->width = w;
}

static void a1(Pen *p)
{
	fixed(p);
	pen_segment(p, CX, 0, CX, AFIG);
}

/* the stem shared by 2 and 3 with a bar and teeth along the top */
static void stem_teeth(Pen *p, int teeth)
{
	fixed(p);
	double x0 = 170, bar = 470, x1 = teeth == 1 ? 440 : 470;
	pen_segment(p, x0, 0, x0, AFIG);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x0, bar, 0,
	      x1, bar, 50,
	      x1, AFIG, 0);
	if (teeth == 2)
		pen_segment(p, 320, bar, 320, AFIG - 40);
}

static void a2(Pen *p) { stem_teeth(p, 1); }
static void a3(Pen *p) { stem_teeth(p, 2); }

static void a4(Pen *p)
{
	fixed(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      450, AFIG - HS, 0,
	      200, AFIG - HS, 80,
	      200, 380, 80,
	      390, 380, 0);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      390, 380, 0,
	      140, 380, 100,
	      140, HS, 70,
	      470, HS, 0);
}

static void a5(Pen *p)
{
	fixed(p);
	pen_ring(p, CX, 270, 165, 230);
}

static void a6(Pen *p)
{
	fixed(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      110, AFIG - HS, 0,
	      440, AFIG - HS, 90,
	      440, 0, 0);
}

static void a7(Pen *p)
{
	fixed(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      105, AFIG, 0,
	      CX, HS, 0,
	      DIGIT_ADV - 105, AFIG, 0);
}

static void a8(Pen *p)
{
	fixed(p);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      105, 0, 0,
	      CX, AFIG - HS, 0,
	      DIGIT_ADV - 105, 0, 0);
}

static void a9(Pen *p)
{
	fixed(p);
	pen_ring(p, 270, 465, 140, 140);
	pen_segment(p, 410, 465, 410, 0);
}

static const SymbolDef defs[] = {
	{"zero", {'0'}, d0, true},
	{"one", {'1'}, d1, true},
	{"two", {'2'}, d2, true},
	{"three", {'3'}, d3, true},
	{"four", {'4'}, d4, true},
	{"five", {'5'}, d5, true},
	{"six", {'6'}, d6, true},
	{"seven", {'7'}, d7, true},
	{"eight", {'8'}, d8, true},
	{"nine", {'9'}, d9, true},
	/* the persian forms of 4, 5 and 6 differ, so those stay unmapped */
	{"zero.ar", {0x0660, 0x06F0}, a0, true},
	{"one.ar", {0x0661, 0x06F1}, a1, true},
	{"two.ar", {0x0662, 0x06F2}, a2, true},
	{"three.ar", {0x0663, 0x06F3}, a3, true},
	{"four.ar", {0x0664}, a4, true},
	{"five.ar", {0x0665}, a5, true},
	{"six.ar", {0x0666}, a6, true},
	{"seven.ar", {0x0667, 0x06F7}, a7, true},
	{"eight.ar", {0x0668, 0x06F8}, a8, true},
	{"nine.ar", {0x0669, 0x06F9}, a9, true},
};

const SymbolDef *digit_defs(int *n)
{
	*n = (int)(sizeof defs / sizeof *defs);
	return defs;
}
