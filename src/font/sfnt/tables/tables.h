#ifndef BFA_FONT_SFNT_TABLES_H
#define BFA_FONT_SFNT_TABLES_H

#include "base/buf.h"
#include "font/glyph/font.h"
#include "font/sfnt/stats.h"

/* each writer appends one complete table to out */
void table_head(const Font *f, const Stats *st, Buf *out);
void table_hhea(const Font *f, const Stats *st, Buf *out);
void table_maxp(const Font *f, const Stats *st, Buf *out);
void table_os2(const Font *f, const Stats *st, Buf *out);
void table_name(const Font *f, const Stats *st, Buf *out);
void table_cmap(const Font *f, const Stats *st, Buf *out);
void table_hmtx(const Font *f, const Stats *st, Buf *out);
void table_post(const Font *f, const Stats *st, Buf *out);
void table_gdef(const Font *f, const Stats *st, Buf *out);
void table_gsub(const Font *f, const Stats *st, Buf *out);

/* glyf and loca come out together */
void table_glyf(const Font *f, const Stats *st, Buf *glyf, Buf *loca);

/* offset of head.checkSumAdjustment inside the head table */
#define HEAD_CHECKSUM_ADJ_OFFSET 8

#endif
