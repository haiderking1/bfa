#include "font/design/letter.h"
#include "font/design/letters/letters.h"

#include <stddef.h>

#define DOTS(a, b) {a, b, MARK_NONE, -1}
#define WITH(m) {0, 0, m, -1}

static const LetterDef defs[] = {
	{0x0621, body_hamza, DOTS(0, 0)},
	{0x0622, body_alef, WITH(MARK_MADDA)},
	{0x0623, body_alef, WITH(MARK_HAMZA_ABOVE)},
	{0x0624, body_waw, WITH(MARK_HAMZA_ABOVE)},
	{0x0625, body_alef, WITH(MARK_HAMZA_BELOW)},
	{0x0626, body_yeh, WITH(MARK_HAMZA_ABOVE)},
	{0x0627, body_alef, DOTS(0, 0)},
	{0x0628, body_beh, DOTS(0, 1)},
	{0x0629, body_heh, DOTS(2, 0)},
	{0x062A, body_beh, DOTS(2, 0)},
	{0x062B, body_beh, DOTS(3, 0)},
	{0x062C, body_hah, DOTS(0, 1)},
	{0x062D, body_hah, DOTS(0, 0)},
	{0x062E, body_hah, DOTS(1, 0)},
	{0x062F, body_dal, DOTS(0, 0)},
	{0x0630, body_dal, DOTS(1, 0)},
	{0x0631, body_reh, DOTS(0, 0)},
	{0x0632, body_reh, DOTS(1, 0)},
	{0x0633, body_seen, DOTS(0, 0)},
	{0x0634, body_seen, DOTS(3, 0)},
	{0x0635, body_sad, DOTS(0, 0)},
	{0x0636, body_sad, DOTS(1, 0)},
	{0x0637, body_tah, DOTS(0, 0)},
	{0x0638, body_tah, DOTS(1, 0)},
	{0x0639, body_ain, DOTS(0, 0)},
	{0x063A, body_ain, DOTS(1, 0)},
	{0x0640, body_tatweel, DOTS(0, 0)},
	{0x0641, body_feh, DOTS(1, 0)},
	{0x0642, body_qaf, DOTS(2, 0)},
	{0x0643, body_kaf, DOTS(0, 0)},
	{0x0644, body_lam, DOTS(0, 0)},
	{0x0645, body_meem, DOTS(0, 0)},
	{0x0646, body_noon, DOTS(1, 0)},
	{0x0647, body_heh, DOTS(0, 0)},
	{0x0648, body_waw, DOTS(0, 0)},
	{0x0649, body_yeh, DOTS(0, 0)},
	{0x064A, body_yeh, DOTS(0, 2)},
	{0x067E, body_beh, DOTS(0, 3)},
	{0x0686, body_hah, DOTS(0, 3)},
	{0x0698, body_reh, DOTS(3, 0)},
	{0x06A9, body_keheh, DOTS(0, 0)},
	{0x06AF, body_gaf, DOTS(0, 0)},
	{0x06CC, body_yeh, {0, 0, MARK_NONE, 2}}, /* dotless when final */
};

const LetterDef *letter_defs(int *n)
{
	*n = (int)(sizeof defs / sizeof *defs);
	return defs;
}

const LetterDef *letter_def(uint32_t cp)
{
	for (size_t i = 0; i < sizeof defs / sizeof *defs; i++)
		if (defs[i].cp == cp)
			return &defs[i];
	return NULL;
}
