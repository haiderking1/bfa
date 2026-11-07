#include "check.h"
#include "base/buf.h"

int main(void)
{
	Buf b;
	buf_init(&b);
	buf_u8(&b, 0xAB);
	buf_u16(&b, 0x1234);
	buf_i16(&b, -2);
	buf_u32(&b, 0xDEADBEEF);
	buf_i64(&b, 0x0102030405060708LL);
	CHECK_EQ(b.len, 1 + 2 + 2 + 4 + 8);
	CHECK_EQ(b.data[0], 0xAB);
	CHECK_EQ(rd_u16(b.data + 1), 0x1234);
	CHECK_EQ(rd_u16(b.data + 3), 0xFFFE);
	CHECK_EQ(rd_u32(b.data + 5), 0xDEADBEEF);
	CHECK_EQ(rd_u32(b.data + 9), 0x01020304);
	CHECK_EQ(rd_u32(b.data + 13), 0x05060708);
	buf_pad4(&b);
	CHECK_EQ(b.len, 20);
	buf_set_u16(&b, 1, 0xBEEF);
	CHECK_EQ(rd_u16(b.data + 1), 0xBEEF);
	buf_set_u32(&b, 5, 7);
	CHECK_EQ(rd_u32(b.data + 5), 7);
	for (int i = 0; i < 10000; i++)
		buf_u8(&b, (uint8_t)i);
	CHECK_EQ(b.len, 10020);
	CHECK_EQ(b.data[10019], (uint8_t)9999);
	buf_free(&b);
	return CHECK_DONE();
}
