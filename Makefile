CC      = clang
CFLAGS ?= -O2 -g
CFLAGS += -std=c17 -Wall -Wextra -Wpedantic -Wshadow -Wstrict-prototypes \
          -Wmissing-prototypes -D_DEFAULT_SOURCE -Isrc -MMD -MP
LDLIBS  = -lm
BUILD   = build

rwildcard = $(foreach d,$(wildcard $(1:=/*)),$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))

LIB_SRC  := $(call rwildcard,src,*.c)
LIB_OBJ  := $(LIB_SRC:%.c=$(BUILD)/%.o)
LIB      := $(BUILD)/libbfa.a

TOOL_SRC := $(wildcard tools/*.c)
TOOLS    := $(TOOL_SRC:tools/%.c=$(BUILD)/bin/%)

TEST_SRC := $(foreach f,$(call rwildcard,tests,*.c),$(if $(filter test_%,$(notdir $f)),$f))
TESTS    := $(TEST_SRC:tests/%.c=$(BUILD)/tests/%)

FONT     := $(BUILD)/font/BfaArabic-Regular.ttf

.PHONY: all font test clean
.SECONDARY:

all: $(TOOLS)

font: $(FONT)

$(FONT): $(BUILD)/bin/bfa-font
	@mkdir -p $(dir $@)
	$< -o $@ -p $(BUILD)/font/glyphs.png

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB): $(LIB_OBJ)
	@mkdir -p $(dir $@)
	$(AR) rcs $@ $^

$(BUILD)/bin/%: $(BUILD)/tools/%.o $(LIB)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $^ $(LDLIBS) -o $@

$(BUILD)/tests/%: $(BUILD)/tests/%.o $(LIB)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -Itests $^ $(LDLIBS) -o $@

$(BUILD)/tests/%.o: CFLAGS += -Itests

test: $(TESTS)
	@fail=0; for t in $(TESTS); do \
	  if $$t; then echo "pass  $$t"; else echo "FAIL  $$t"; fail=1; fi; \
	done; exit $$fail

clean:
	rm -rf $(BUILD)

-include $(LIB_OBJ:.o=.d) $(TOOL_SRC:%.c=$(BUILD)/%.d) $(TEST_SRC:%.c=$(BUILD)/%.d)
