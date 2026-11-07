#ifndef BFA_FONT_SHAPE_JOINING_H
#define BFA_FONT_SHAPE_JOINING_H

#include <stdint.h>

typedef enum {
	JT_U, /* non-joining */
	JT_R, /* joins only to the previous letter (right side) */
	JT_D, /* joins on both sides */
	JT_C, /* join-causing, like tatweel */
	JT_T, /* transparent: marks */
} JoinType;

typedef enum { FORM_ISOL, FORM_FINA, FORM_INIT, FORM_MEDI, FORM_COUNT } Form;

typedef struct {
	uint32_t cp;
	JoinType jt;
	const char *name;          /* base glyph name */
	uint32_t pres[FORM_COUNT]; /* presentation form codepoints, 0 if none */
} ArabicLetter;

typedef struct {
	uint32_t alef;             /* the alef variant that follows lam */
	const char *name;
	uint32_t isol, fina;       /* presentation forms of the ligature */
} LamAlef;

const ArabicLetter *arabic_letters(int *n);
const ArabicLetter *arabic_letter(uint32_t cp);
const LamAlef *lam_alefs(int *n);

const char *form_suffix(Form f); /* "", ".fina", ".init", ".medi" */

#define CP_LAM 0x0644

#endif
