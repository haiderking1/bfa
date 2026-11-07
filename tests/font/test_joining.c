#include "check.h"
#include "font/design/letter.h"
#include "font/shape/joining.h"

int main(void)
{
	int n;
	const ArabicLetter *al = arabic_letters(&n);
	CHECK(n > 36);
	for (int i = 0; i < n; i++) {
		int forms = 0;
		for (int f = 0; f < FORM_COUNT; f++)
			forms += al[i].pres[f] != 0;
		if (al[i].jt == JT_D)
			CHECK_EQ(forms, 4);
		else if (al[i].jt == JT_R)
			CHECK_EQ(forms, 2);
		CHECK(letter_def(al[i].cp) != NULL);
		CHECK(arabic_letter(al[i].cp) == &al[i]);
		for (int j = 0; j < i; j++)
			CHECK(al[j].cp != al[i].cp);
	}
	int nl;
	const LamAlef *la = lam_alefs(&nl);
	CHECK_EQ(nl, 4);
	for (int i = 0; i < nl; i++) {
		const ArabicLetter *a = arabic_letter(la[i].alef);
		CHECK(a && a->jt == JT_R);
		CHECK_EQ(la[i].fina, la[i].isol + 1);
	}
	return CHECK_DONE();
}
