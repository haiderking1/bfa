#ifndef BFA_FONT_DESIGN_STYLE_H
#define BFA_FONT_DESIGN_STYLE_H

/* the whole look in one place. units are 1/1000 em. */

#define UPM 1000

#define ST 74.0             /* stroke width */
#define HS (ST / 2)         /* half stroke */
#define BY HS               /* baseline stroke centerline (bottom sits on 0) */

#define TOP 720.0           /* alef, lam, kaf and tah stems */
#define TOOTH 300.0         /* tops of teeth */
#define SEEN_TOOTH 250.0    /* seen's teeth sit a bit lower */
#define LOOP 330.0          /* tops of feh/qaf/waw/sad heads */
#define DESC -340.0         /* bottom edge of tails */
#define DEEP -400.0         /* bottom edge of jeem/ain bowls */

#define R 60.0              /* default corner radius on centerlines */
#define BOWL_R 140.0        /* radius for round bowls */

#define DOT_R 56.0
#define DOT_GAP 28.0        /* between neighbor dots */
#define DOT_CLEAR 62.0      /* from ink to a dot's edge */

#define SB 58.0             /* side bearing on a free side */
#define JX 44.0             /* baseline run on a joining side */
#define OVL 12.0            /* connectors reach past the advance so joins
			       never show a hairline seam */

#define MARK_ST (ST * 0.8)  /* stroke of hamza, madda and tashkeel */

#define FLAT_TOL 0.25       /* curve flattening for skeletons */

#endif
