#include "font/sfnt/tables/tables.h"
#include "font/sfnt/tables/otl.h"
#include "base/mem.h"

#include <stdlib.h>
#include <string.h>

enum { LOOKUP_SINGLE = 1, LOOKUP_LIGATURE = 4 };
enum { IGNORE_MARKS = 0x0008 };

static int pair_cmp(const void *a, const void *b)
{
	return ((const SubstPair *)a)->from - ((const SubstPair *)b)->from;
}

static void single_subtable(const SingleFeature *sf, Buf *out)
{
	SubstPair *p = xmalloc((size_t)(sf->n ? sf->n : 1) * sizeof *p);
	memcpy(p, sf->p, (size_t)sf->n * sizeof *p);
	qsort(p, (size_t)sf->n, sizeof *p, pair_cmp);
	int *cov = xmalloc((size_t)(sf->n ? sf->n : 1) * sizeof *cov);
	for (int i = 0; i < sf->n; i++)
		cov[i] = p[i].from;
	buf_u16(out, 2);
	buf_u16(out, (uint16_t)(6 + 2 * sf->n)); /* coverage after the array */
	buf_u16(out, (uint16_t)sf->n);
	for (int i = 0; i < sf->n; i++)
		buf_u16(out, (uint16_t)p[i].to);
	otl_coverage(out, cov, sf->n);
	free(cov);
	free(p);
}

static int rule_cmp(const void *a, const void *b)
{
	const LigRule *x = a, *y = b;
	if (x->comp[0] != y->comp[0])
		return x->comp[0] - y->comp[0];
	return y->ncomp - x->ncomp; /* longest match first */
}

static void lig_subtable(const LigFeature *lf, Buf *out)
{
	LigRule *r = xmalloc((size_t)(lf->n ? lf->n : 1) * sizeof *r);
	memcpy(r, lf->r, (size_t)lf->n * sizeof *r);
	qsort(r, (size_t)lf->n, sizeof *r, rule_cmp);
	int *first = xmalloc((size_t)(lf->n ? lf->n : 1) * sizeof *first);
	int nset = 0;
	for (int i = 0; i < lf->n; i++)
		if (!nset || first[nset - 1] != r[i].comp[0])
			first[nset++] = r[i].comp[0];

	Blobs sets = {0};
	for (int s = 0, i = 0; s < nset; s++) {
		int j = i;
		while (j < lf->n && r[j].comp[0] == first[s])
			j++;
		Buf *set = blobs_add(&sets);
		int cnt = j - i;
		buf_u16(set, (uint16_t)cnt);
		size_t off = 2 + 2 * (size_t)cnt;
		for (int k = i; k < j; k++) {
			buf_u16(set, (uint16_t)off);
			off += 4 + 2 * (size_t)(r[k].ncomp - 1);
		}
		for (int k = i; k < j; k++) {
			buf_u16(set, (uint16_t)r[k].lig);
			buf_u16(set, (uint16_t)r[k].ncomp);
			for (int c = 1; c < r[k].ncomp; c++)
				buf_u16(set, (uint16_t)r[k].comp[c]);
		}
		i = j;
	}
	size_t head = 6 + 2 * (size_t)nset;
	size_t cov_off = head + blobs_size(&sets);
	buf_u16(out, 1);
	buf_u16(out, (uint16_t)cov_off);
	buf_u16(out, (uint16_t)nset);
	size_t off = head;
	for (int s = 0; s < nset; s++) {
		buf_u16(out, (uint16_t)off);
		off += sets.item[s].len;
	}
	for (int s = 0; s < nset; s++)
		buf_bytes(out, sets.item[s].data, sets.item[s].len);
	otl_coverage(out, first, nset);
	blobs_free(&sets);
	free(first);
	free(r);
}

typedef struct {
	char tag[5];
	int lookup;
} FeatRef;

static int feat_cmp(const void *a, const void *b)
{
	return memcmp(((const FeatRef *)a)->tag, ((const FeatRef *)b)->tag, 4);
}

void table_gsub(const Font *f, const Stats *st, Buf *out)
{
	(void)st;
	int nl = f->nsingle + f->nlig;
	Blobs lookups = {0};
	FeatRef *fr = xmalloc((size_t)(nl ? nl : 1) * sizeof *fr);
	for (int i = 0; i < nl; i++) {
		Buf *lk = blobs_add(&lookups);
		Buf sub;
		buf_init(&sub);
		int type, flag;
		if (i < f->nsingle) {
			single_subtable(&f->single[i], &sub);
			type = LOOKUP_SINGLE;
			flag = 0;
			memcpy(fr[i].tag, f->single[i].tag, 5);
		} else {
			const LigFeature *lf = &f->lig[i - f->nsingle];
			lig_subtable(lf, &sub);
			type = LOOKUP_LIGATURE;
			flag = lf->ignore_marks ? IGNORE_MARKS : 0;
			memcpy(fr[i].tag, lf->tag, 5);
		}
		fr[i].lookup = i;
		buf_u16(lk, (uint16_t)type);
		buf_u16(lk, (uint16_t)flag);
		buf_u16(lk, 1);
		buf_u16(lk, 8);
		buf_bytes(lk, sub.data, sub.len);
		buf_free(&sub);
	}
	qsort(fr, (size_t)nl, sizeof *fr, feat_cmp);

	Buf scripts, feats, lklist;
	buf_init(&scripts);
	buf_init(&feats);
	buf_init(&lklist);
	otl_scripts(&scripts, nl);

	/* FeatureList: records then one feature table per record */
	buf_u16(&feats, (uint16_t)nl);
	size_t foff = 2 + 6 * (size_t)nl;
	for (int i = 0; i < nl; i++) {
		buf_bytes(&feats, fr[i].tag, 4);
		buf_u16(&feats, (uint16_t)(foff + 6 * (size_t)i));
	}
	for (int i = 0; i < nl; i++) {
		buf_u16(&feats, 0);     /* featureParams */
		buf_u16(&feats, 1);
		buf_u16(&feats, (uint16_t)fr[i].lookup);
	}

	buf_u16(&lklist, (uint16_t)nl);
	size_t loff = 2 + 2 * (size_t)nl;
	for (int i = 0; i < nl; i++) {
		buf_u16(&lklist, (uint16_t)loff);
		loff += lookups.item[i].len;
	}
	for (int i = 0; i < nl; i++)
		buf_bytes(&lklist, lookups.item[i].data, lookups.item[i].len);

	buf_u16(out, 1);
	buf_u16(out, 0);
	buf_u16(out, 10);
	buf_u16(out, (uint16_t)(10 + scripts.len));
	buf_u16(out, (uint16_t)(10 + scripts.len + feats.len));
	buf_bytes(out, scripts.data, scripts.len);
	buf_bytes(out, feats.data, feats.len);
	buf_bytes(out, lklist.data, lklist.len);

	buf_free(&scripts);
	buf_free(&feats);
	buf_free(&lklist);
	blobs_free(&lookups);
	free(fr);
}
