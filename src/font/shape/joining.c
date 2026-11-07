#include "font/shape/joining.h"

#include <stddef.h>

#define R2(b) {b, b + 1, 0, 0}
#define D4(b) {b, b + 1, b + 2, b + 3}

static const ArabicLetter letters[] = {
	{0x0621, JT_U, "hamza", {0xFE80, 0, 0, 0}},
	{0x0622, JT_R, "alefMadda", R2(0xFE81)},
	{0x0623, JT_R, "alefHamzaAbove", R2(0xFE83)},
	{0x0624, JT_R, "wawHamza", R2(0xFE85)},
	{0x0625, JT_R, "alefHamzaBelow", R2(0xFE87)},
	{0x0626, JT_D, "yehHamza", D4(0xFE89)},
	{0x0627, JT_R, "alef", R2(0xFE8D)},
	{0x0628, JT_D, "beh", D4(0xFE8F)},
	{0x0629, JT_R, "tehMarbuta", R2(0xFE93)},
	{0x062A, JT_D, "teh", D4(0xFE95)},
	{0x062B, JT_D, "theh", D4(0xFE99)},
	{0x062C, JT_D, "jeem", D4(0xFE9D)},
	{0x062D, JT_D, "hah", D4(0xFEA1)},
	{0x062E, JT_D, "khah", D4(0xFEA5)},
	{0x062F, JT_R, "dal", R2(0xFEA9)},
	{0x0630, JT_R, "thal", R2(0xFEAB)},
	{0x0631, JT_R, "reh", R2(0xFEAD)},
	{0x0632, JT_R, "zain", R2(0xFEAF)},
	{0x0633, JT_D, "seen", D4(0xFEB1)},
	{0x0634, JT_D, "sheen", D4(0xFEB5)},
	{0x0635, JT_D, "sad", D4(0xFEB9)},
	{0x0636, JT_D, "dad", D4(0xFEBD)},
	{0x0637, JT_D, "tah", D4(0xFEC1)},
	{0x0638, JT_D, "zah", D4(0xFEC5)},
	{0x0639, JT_D, "ain", D4(0xFEC9)},
	{0x063A, JT_D, "ghain", D4(0xFECD)},
	{0x0640, JT_C, "tatweel", {0, 0, 0, 0}},
	{0x0641, JT_D, "feh", D4(0xFED1)},
	{0x0642, JT_D, "qaf", D4(0xFED5)},
	{0x0643, JT_D, "kaf", D4(0xFED9)},
	{0x0644, JT_D, "lam", D4(0xFEDD)},
	{0x0645, JT_D, "meem", D4(0xFEE1)},
	{0x0646, JT_D, "noon", D4(0xFEE5)},
	{0x0647, JT_D, "heh", D4(0xFEE9)},
	{0x0648, JT_R, "waw", R2(0xFEED)},
	/* dual-joining in unicode; its joined forms live in forms-a */
	{0x0649, JT_D, "alefMaksura", {0xFEEF, 0xFEF0, 0xFBE8, 0xFBE9}},
	{0x064A, JT_D, "yeh", D4(0xFEF1)},
	{0x067E, JT_D, "peh", D4(0xFB56)},
	{0x0686, JT_D, "tcheh", D4(0xFB7A)},
	{0x0698, JT_R, "jeh", R2(0xFB8A)},
	{0x06A9, JT_D, "keheh", D4(0xFB8E)},
	{0x06AF, JT_D, "gaf", D4(0xFB92)},
	{0x06CC, JT_D, "farsiYeh", D4(0xFBFC)},
};

static const LamAlef lamalefs[] = {
	{0x0622, "lam_alefMadda", 0xFEF5, 0xFEF6},
	{0x0623, "lam_alefHamzaAbove", 0xFEF7, 0xFEF8},
	{0x0625, "lam_alefHamzaBelow", 0xFEF9, 0xFEFA},
	{0x0627, "lam_alef", 0xFEFB, 0xFEFC},
};

const ArabicLetter *arabic_letters(int *n)
{
	*n = (int)(sizeof letters / sizeof *letters);
	return letters;
}

const ArabicLetter *arabic_letter(uint32_t cp)
{
	for (size_t i = 0; i < sizeof letters / sizeof *letters; i++)
		if (letters[i].cp == cp)
			return &letters[i];
	return NULL;
}

const LamAlef *lam_alefs(int *n)
{
	*n = (int)(sizeof lamalefs / sizeof *lamalefs);
	return lamalefs;
}

const char *form_suffix(Form f)
{
	static const char *s[FORM_COUNT] = {"", ".fina", ".init", ".medi"};
	return s[f];
}
