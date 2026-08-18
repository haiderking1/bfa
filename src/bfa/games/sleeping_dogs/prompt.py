"""Sleeping Dogs: Definitive Edition translation brief and term lock."""

from __future__ import annotations

from dataclasses import replace

from bfa.config import Settings

SLEEPING_DOGS_TRANSLATION_BRIEF = """
This batch is from Sleeping Dogs: Definitive Edition, an open-world crime game
set in Hong Kong. The player character Wei Shen is an undercover cop inside the
Sun On Yee triad. Keep the Hong Kong street-crime register: triad slang, cop
radio, mission UI, and angry spoken lines. Do not flatten "as shit",
"fucked up", "throwing your weight around", or similar into polite MSA.

Wei Shen is a man. Arabic addressing him is always masculine
(عد / تعال / انتظر — never عودي / تعالي / انتظري).

Locked character names — use these spellings only:
Wei Shen = وي شين
Jackie = جاكي
Winston = وينستون
Peggy = بيغي
Dogeyes = دوج آيز
Horseface = هورس فيس
Pendrew = بندرو
Raymond = رايموند
Uncle Po = العم بو
Big Smile Lee = بيغ سمايل لي
Zi Wai = زي واي
Sun On Yee = صن أون يي
Triad = الثالوث
Orange Lotus = اللوتس البرتقالي
Face (the meter / reputation) = الوجه

Locked gameplay terms:
vault / vaulting / Vault Attack = القفز فوق الحاجز / هجوم القفز
(parkour over cover or a railing — NEVER خزنة, صندوق, or a bank vault)
bug a phone / bug the payphone = تنصت / جهاز تنصت (NEVER حشرة unless the
English source is actually an insect)
""".strip()


def apply_sleeping_dogs_brief(settings: Settings) -> Settings:
    """Attach the Sleeping Dogs brief unless the caller already set one."""
    if settings.translation_brief.strip():
        return settings
    return replace(settings, translation_brief=SLEEPING_DOGS_TRANSLATION_BRIEF)
