#ifndef BFA_BASE_VEC_H
#define BFA_BASE_VEC_H

#include <math.h>

typedef struct {
	double x, y;
} Vec2;

static inline Vec2 v2(double x, double y) { return (Vec2){x, y}; }
static inline Vec2 v2_add(Vec2 a, Vec2 b) { return v2(a.x + b.x, a.y + b.y); }
static inline Vec2 v2_sub(Vec2 a, Vec2 b) { return v2(a.x - b.x, a.y - b.y); }
static inline Vec2 v2_scale(Vec2 a, double s) { return v2(a.x * s, a.y * s); }
static inline double v2_dot(Vec2 a, Vec2 b) { return a.x * b.x + a.y * b.y; }
static inline double v2_cross(Vec2 a, Vec2 b) { return a.x * b.y - a.y * b.x; }
static inline double v2_len(Vec2 a) { return sqrt(a.x * a.x + a.y * a.y); }
static inline double v2_dist(Vec2 a, Vec2 b) { return v2_len(v2_sub(a, b)); }
static inline Vec2 v2_perp(Vec2 a) { return v2(-a.y, a.x); }
static inline Vec2 v2_lerp(Vec2 a, Vec2 b, double t)
{
	return v2(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t);
}
static inline Vec2 v2_norm(Vec2 a)
{
	double l = v2_len(a);
	return l > 0 ? v2_scale(a, 1.0 / l) : v2(0, 0);
}

#endif
