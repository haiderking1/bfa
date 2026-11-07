#include "font/preview/png.h"
#include "base/buf.h"

#include <stdio.h>

static uint32_t crc_table[256];

static void crc_init(void)
{
	for (uint32_t n = 0; n < 256; n++) {
		uint32_t c = n;
		for (int k = 0; k < 8; k++)
			c = c & 1 ? 0xEDB88320u ^ (c >> 1) : c >> 1;
		crc_table[n] = c;
	}
}

static uint32_t crc(const uint8_t *p, size_t n)
{
	uint32_t c = 0xFFFFFFFFu;
	for (size_t i = 0; i < n; i++)
		c = crc_table[(c ^ p[i]) & 0xFF] ^ (c >> 8);
	return c ^ 0xFFFFFFFFu;
}

static void chunk(Buf *out, const char *type, const uint8_t *data, size_t n)
{
	buf_u32(out, (uint32_t)n);
	size_t start = out->len;
	buf_bytes(out, type, 4);
	buf_bytes(out, data, n);
	buf_u32(out, crc(out->data + start, n + 4));
}

/* zlib stream made of stored deflate blocks: no compression, no deps */
static void zlib_stored(Buf *z, const uint8_t *p, size_t n)
{
	buf_u8(z, 0x78);
	buf_u8(z, 0x01);
	uint32_t a = 1, b = 0;
	size_t off = 0;
	do {
		size_t len = n - off > 65535 ? 65535 : n - off;
		buf_u8(z, off + len == n ? 1 : 0);
		buf_u8(z, (uint8_t)len);
		buf_u8(z, (uint8_t)(len >> 8));
		buf_u8(z, (uint8_t)~len);
		buf_u8(z, (uint8_t)(~len >> 8));
		buf_bytes(z, p + off, len);
		for (size_t i = 0; i < len; i++) {
			a = (a + p[off + i]) % 65521;
			b = (b + a) % 65521;
		}
		off += len;
	} while (off < n);
	buf_u32(z, b << 16 | a);
}

int png_write(const char *path, const Image *im)
{
	crc_init();
	Buf raw, z, out;
	buf_init(&raw);
	buf_init(&z);
	buf_init(&out);
	for (int y = 0; y < im->h; y++) {
		buf_u8(&raw, 0);
		for (int x = 0; x < im->w; x++)
			buf_u8(&raw, (uint8_t)(255 - im->px[(long)y * im->w + x]));
	}
	zlib_stored(&z, raw.data, raw.len);

	static const uint8_t sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
	buf_bytes(&out, sig, 8);
	Buf ihdr;
	buf_init(&ihdr);
	buf_u32(&ihdr, (uint32_t)im->w);
	buf_u32(&ihdr, (uint32_t)im->h);
	buf_u8(&ihdr, 8); /* depth */
	buf_u8(&ihdr, 0); /* grayscale */
	buf_u8(&ihdr, 0);
	buf_u8(&ihdr, 0);
	buf_u8(&ihdr, 0);
	chunk(&out, "IHDR", ihdr.data, ihdr.len);
	chunk(&out, "IDAT", z.data, z.len);
	chunk(&out, "IEND", NULL, 0);

	int rc = -1;
	FILE *fp = fopen(path, "wb");
	if (fp) {
		rc = fwrite(out.data, 1, out.len, fp) == out.len ? 0 : -1;
		if (fclose(fp))
			rc = -1;
	}
	buf_free(&ihdr);
	buf_free(&raw);
	buf_free(&z);
	buf_free(&out);
	return rc;
}
