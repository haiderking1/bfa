#ifndef BFA_FONT_INK_FIELD_H
#define BFA_FONT_INK_FIELD_H

/* signed distance samples on a regular grid, in font units. < 0 is ink. */
typedef struct {
	double x0, y0; /* font coords of node (0,0) */
	double step;   /* font units between nodes */
	int nx, ny;
	float *d;
} Field;

void field_init(Field *f, double xmin, double ymin, double xmax, double ymax,
		double step);
void field_free(Field *f);

static inline float *field_at(Field *f, int i, int j)
{
	return &f->d[(long)j * f->nx + i];
}

#endif
