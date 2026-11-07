#include "font/design/marks/marks.h"
#include "font/design/parts.h"
#include "font/design/style.h"

#define MS (MARK_ST * 0.85)
#define MH (MS / 2)

/* fatha and kasra are the same short slanted stroke */
static void slash_at(Pen *p, double y)
{
	pen_segment(p, -85, y + MH, 85, y + 75);
}

static void fatha(Pen *p, double y) { slash_at(p, y); }
static void kasra(Pen *p, double y) { slash_at(p, y - 75 - MH); }

static void fathatan(Pen *p, double y)
{
	slash_at(p, y);
	slash_at(p, y + 105);
}

static void kasratan(Pen *p, double y)
{
	slash_at(p, y - 75 - MH);
	slash_at(p, y - 180 - MH);
}

/* a little waw: an eye with a tail */
static void damma_at(Pen *p, double x, double y, double k)
{
	double r = 42 * k;
	pen_ring(p, x, y + 150 * k - r, r, r);
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      x + r, y + 150 * k - r, 0,
	      x + r, y + MH + 10, 40 * k,
	      x - 70 * k, y + MH, 0);
}

static void damma(Pen *p, double y) { damma_at(p, 0, y, 1); }

static void dammatan(Pen *p, double y)
{
	damma_at(p, -70, y, 0.85);
	damma_at(p, 75, y, 0.85);
}

static void shadda(Pen *p, double y)
{
	double t = y + 120;
	RPATH(p, CAP_FLAT, CAP_FLAT,
	      -105, t, 0,
	      -105, y + MH, 30,
	      105, y + MH, 30,
	      105, t, 0);
	pen_segment(p, 0, y + MH, 0, t - 15);
}

static void sukun(Pen *p, double y)
{
	pen_ring(p, 0, y + 60, 50, 50);
}

static void madda(Pen *p, double y) { part_madda(p, 0, y); }
static void hamza_above(Pen *p, double y) { part_hamza(p, 0, y, HAMZA_MARK_H); }
static void hamza_below(Pen *p, double y) { part_hamza(p, 0, y - HAMZA_MARK_H, HAMZA_MARK_H); }

static void alef_above(Pen *p, double y)
{
	pen_segment(p, 0, y, 0, y + 190);
}

static const MarkDef defs[] = {
	{"fathatan", 0x064B, MARK_ABOVE, fathatan},
	{"dammatan", 0x064C, MARK_ABOVE, dammatan},
	{"kasratan", 0x064D, MARK_BELOW, kasratan},
	{"fatha", 0x064E, MARK_ABOVE, fatha},
	{"damma", 0x064F, MARK_ABOVE, damma},
	{"kasra", 0x0650, MARK_BELOW, kasra},
	{"shadda", 0x0651, MARK_ABOVE, shadda},
	{"sukun", 0x0652, MARK_ABOVE, sukun},
	{"maddaabove", 0x0653, MARK_ABOVE, madda},
	{"hamzaabove", 0x0654, MARK_ABOVE, hamza_above},
	{"hamzabelow", 0x0655, MARK_BELOW, hamza_below},
	{"alefabove", 0x0670, MARK_ABOVE, alef_above},
};

const MarkDef *mark_defs(int *n)
{
	*n = (int)(sizeof defs / sizeof *defs);
	return defs;
}
