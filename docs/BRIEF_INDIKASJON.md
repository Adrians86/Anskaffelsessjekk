# Anskaffelsessjekk — Mini-brief "Språk: indikasjon, ikke konklusjon"

Partner directive · 2026-07-22 · main = 77e9d095 (0.5.0). Legal red-team finding. All UI Norwegian
(bokmål).

## Bakgrunn (hvorfor)
Jurist-perspektiv i ekspertpanelet: en «vesentlig endring»-vurdering framstilt som KONKLUSJON
(«UGYLDIG») med en prosentgrense er FALSK PRESISJON. Vesentlig endring (FOA §28-1, C-454/06
Pressetext) er en kompleks juridisk skjønnsvurdering — ikke en terskel i prosent. Et system som
«konkluderer» kan lede saksbehandler galt og skape ansvar. Gjør språket til INDIKASJON som peker
mot behov for juridisk vurdering — aldri en juridisk konklusjon. Styrker posisjoneringen
«beslutningsstøtte, ikke juridisk rådgivning».

## Endringer (kun tekst/etiketter + én caption — ingen logikkendring i motoren)
Gjelder e-post-flyt (2_Avtaler_og_forpliktelser.py) og alle steder gyldighetsvurdering vises
(inkl. Leverandørkort hvis den rendres der):
- Omdøp den strengeste statusen fra «✗ UGYLDIG» til «✗ MULIG UGYLDIG — krever juridisk vurdering»
  (kort chip-variant der plass er knapp: «MULIG UGYLDIG»). Behold rød farge.
- Omformuler de tre utfallene som INDIKASJONER, ikke dommer:
  - GYLDIG → «✓ SANNSYNLIGVIS GYLDIG» — tekst: «Ser ut til å være i samsvar med avtalens
    endringsbestemmelser. Bekreftes av saksbehandler.»
  - KREVER FORMALISERING → behold — tekst: «Avtalen ser ut til å kreve skriftlig tillegg —
    e-posten er varsel, ikke dokumentasjon.»
  - UGYLDIG → «✗ MULIG UGYLDIG — krever juridisk vurdering» — tekst: «Kan innebære en vesentlig
    endring (jf. FOA §28-1). Vesentlig endring er en juridisk skjønnsvurdering som krever ny
    konkurranse — vurder med jurist før du bekrefter.»
- Fast disclaimer-caption under enhver gyldighetsvurdering (én linje, grå):
  «Gyldighetsvurderingen er en indikasjon som støtte for saksbehandler — ikke en juridisk
  konklusjon.»
- Legenden «Gyldighetsvurdering — mulige utfall» oppdateres til de nye tre etikettene.
- «Bekreft» forblir aktiv for alle utfall (hard rule #3 — informerer, blokkerer ikke; uendret).
- Audit-loggen ved bekreftelse tross MULIG UGYLDIG beholdes, men teksten:
  «bekreftet tross indikasjon om mulig vesentlig endring».

## Utenfor scope (ikke rør)
Motorens logikk / terskler / regeldata — INGEN endring. Ren språk-/etikett-endring. Prosentgrensen
internt kan bestå som en HEURISTIKK for å TRIGGE indikasjonen, men må ALDRI presenteres som selve
kriteriet for vesentlig endring i UI-teksten.

## DoD
Oppdater tester som matcher på de gamle etikettene. pytest grønt, ruff rent. Ingen versjonsbump
nødvendig (ingen skjemaendring), men noter i STATUS. CLAUDE.md Current tasks: «Språk
indikasjon-ikke-konklusjon levert (jurist-funn)». Push.

## Acceptance
- E-post-eksempel 3 (utvidelse +45%) viser «✗ MULIG UGYLDIG — krever juridisk vurdering» med
  FOA §28-1-henvisning og «vurder med jurist»-tekst — IKKE en bastant «UGYLDIG».
- Fast disclaimer-caption «indikasjon ... ikke en juridisk konklusjon» vises under vurderingen.
- «Bekreft» fortsatt mulig for alle utfall; audit-tekst oppdatert.
- Ingen logikkendring: samme forpliktelser trigges, kun språket er endret.
