#ifndef BFA_BASE_BUF_H
#define BFA_BASE_BUF_H

#include <stddef.h>
#include <stdint.h>

/* growable byte buffer with big-endian writers (sfnt is big-endian) */
typedef struct {
	uint8_t *data;
	size_t len, cap;
} Buf;

void buf_init(Buf *b);
void buf_free(Buf *b);
void buf_reserve(Buf *b, size_t extra);

void buf_bytes(Buf *b, const void *p, size_t n);
void buf_u8(Buf *b, uint8_t v);
void buf_u16(Buf *b, uint16_t v);
void buf_i16(Buf *b, int16_t v);
void buf_u32(Buf *b, uint32_t v);
void buf_i64(Buf *b, int64_t v);
void buf_zero(Buf *b, size_t n);
void buf_pad4(Buf *b);

void buf_set_u16(Buf *b, size_t off, uint16_t v);
void buf_set_u32(Buf *b, size_t off, uint32_t v);

uint16_t rd_u16(const uint8_t *p);
uint32_t rd_u32(const uint8_t *p);

#endif
