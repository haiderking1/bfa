#ifndef BFA_FONT_SFNT_WRITER_H
#define BFA_FONT_SFNT_WRITER_H

#include "base/buf.h"
#include "font/glyph/font.h"

/* serialize the whole font as a truetype sfnt */
void sfnt_build(const Font *f, Buf *out);
int sfnt_save(const Font *f, const char *path);

uint32_t sfnt_checksum(const uint8_t *p, size_t n);

#endif
