#include "base/buf.h"
#include "base/mem.h"

#include <stdlib.h>
#include <string.h>

void buf_init(Buf *b)
{
	b->data = NULL;
	b->len = b->cap = 0;
}

void buf_free(Buf *b)
{
	free(b->data);
	buf_init(b);
}

void buf_reserve(Buf *b, size_t extra)
{
	if (b->len + extra <= b->cap)
		return;
	size_t c = b->cap ? b->cap : 256;
	while (c < b->len + extra)
		c *= 2;
	b->data = xrealloc(b->data, c);
	b->cap = c;
}

void buf_bytes(Buf *b, const void *p, size_t n)
{
	buf_reserve(b, n);
	memcpy(b->data + b->len, p, n);
	b->len += n;
}

void buf_u8(Buf *b, uint8_t v)
{
	buf_reserve(b, 1);
	b->data[b->len++] = v;
}

void buf_u16(Buf *b, uint16_t v)
{
	buf_reserve(b, 2);
	b->data[b->len++] = (uint8_t)(v >> 8);
	b->data[b->len++] = (uint8_t)v;
}

void buf_i16(Buf *b, int16_t v)
{
	buf_u16(b, (uint16_t)v);
}

void buf_u32(Buf *b, uint32_t v)
{
	buf_u16(b, (uint16_t)(v >> 16));
	buf_u16(b, (uint16_t)v);
}

void buf_i64(Buf *b, int64_t v)
{
	buf_u32(b, (uint32_t)((uint64_t)v >> 32));
	buf_u32(b, (uint32_t)v);
}

void buf_zero(Buf *b, size_t n)
{
	buf_reserve(b, n);
	memset(b->data + b->len, 0, n);
	b->len += n;
}

void buf_pad4(Buf *b)
{
	while (b->len & 3)
		buf_u8(b, 0);
}

void buf_set_u16(Buf *b, size_t off, uint16_t v)
{
	b->data[off] = (uint8_t)(v >> 8);
	b->data[off + 1] = (uint8_t)v;
}

void buf_set_u32(Buf *b, size_t off, uint32_t v)
{
	buf_set_u16(b, off, (uint16_t)(v >> 16));
	buf_set_u16(b, off + 2, (uint16_t)v);
}

uint16_t rd_u16(const uint8_t *p)
{
	return (uint16_t)(p[0] << 8 | p[1]);
}

uint32_t rd_u32(const uint8_t *p)
{
	return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}
