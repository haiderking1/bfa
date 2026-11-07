#ifndef BFA_FONT_DESIGN_LETTERS_H
#define BFA_FONT_DESIGN_LETTERS_H

#include "font/design/pen.h"
#include "font/shape/joining.h"

/* bodies draw in body space: x from 0 to p->bw, baseline stroke on BY.
   connectors and side bearings are added around them by the builder. */

void body_alef(Pen *p, Form f);
void body_tooth(Pen *p, Form f);      /* init/medi of the beh shapes */
void body_beh(Pen *p, Form f);
void body_noon(Pen *p, Form f);
void body_yeh(Pen *p, Form f);        /* alef maksura shape when final */
void body_hah(Pen *p, Form f);
void body_dal(Pen *p, Form f);
void body_reh(Pen *p, Form f);
void body_seen(Pen *p, Form f);
void body_sad(Pen *p, Form f);
void body_tah(Pen *p, Form f);
void body_ain(Pen *p, Form f);
void body_feh(Pen *p, Form f);
void body_qaf(Pen *p, Form f);
void body_kaf(Pen *p, Form f);
void body_keheh(Pen *p, Form f);
void body_gaf(Pen *p, Form f);
void body_lam(Pen *p, Form f);
void body_meem(Pen *p, Form f);
void body_heh(Pen *p, Form f);
void body_waw(Pen *p, Form f);
void body_hamza(Pen *p, Form f);
void body_tatweel(Pen *p, Form f);

/* lam-alef ligature; the alef variant's mark is added by the builder */
void body_lamalef(Pen *p, Form f);

#endif
