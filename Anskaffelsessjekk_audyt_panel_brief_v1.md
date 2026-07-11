# Anskaffelsessjekk — audyt krytyczny, panel ekspertów i brief naprawczy (v1)

**AS North HQ · 2026-07-10 · do wiedzy projektu Anskaffelsessjekk + brief (sekcja 5) do wklejenia agentowi Claude Code**

---

## 1. Werdykt

Demo na anskaffelsessjekk.streamlit.app ma silnik lepszy niż karoserię. Wszystko, co obiecujemy
(sporbarhet, verdi funnet, e-postavtaler, "ingen svart boks"), technicznie DZIAŁA — ale jest
wizualnie schowane. Diagnoza: **to nie brak funkcji, to brak inscenizacji istniejących funkcji.**
Naprawa kosztuje dni, nie miesiące. Zero nowych modułów silnika; nowa ekspozycja + 4 tanie dodatki
z panelu ekspertów (karta bezpieczeństwa, anbefalt handling, eksport CSV, przycisk gjennomgang).

## 2. Audyt ekran po ekranie (ocena okiem kupującego)

| Ekran | Ocena | Główny problem |
|---|---|---|
| Hjem | 3/10 | Spis treści zamiast wyniku; disclaimer najmocniejszym elementem; brak CTA |
| Fakturakontroll | 5/10 | Efekt (F-1003, mail J. Hansena) jest opcjonalnym znaleziskiem; werdykt wygląda jak log; "Hvorfor?" łatwo przeoczyć; po werdykcie brak "co dalej" |
| Avtaler og forpliktelser | 6/10 | Wyróżnik rynkowy (e-postavtaler) wizualnie nieodróżnialny od tła |
| Terskelsjekk | 6/10 | Wynik jako tekst; brak wizualnej ścieżki regime→terskel→konsekvens; nie tłumaczy, czemu reżim pierwszy |
| Styringsinformasjon | 5/10 | Verdi funnet (najlepsza liczba sprzedażowa) niewyróżniona; brak eksportu; brak podziału per dostawca |

## 3. Panel 14 ekspertów — ustalenia (SYMULACJA — red-team, nie dowód rynkowy)

Powtarzające się potrzeby (ranking częstości):
1. **Inscenizacja efektu + eksport danych** — potwierdza plan naprawczy 1:1
2. **Karta "Sikkerhet og databehandling"** (IT-sjef, Forsvaret, personvernombud) — tania, otwiera drzwi trzem personom; bez niej formularz dostawcy IT odrzuca
3. **Raport zbiorczy / eksport** dla controllera i rewizora (CSV teraz; zbiorczy PDF — opcja)
4. **Reglement wewnętrzny** jako warstwa reguł per organizacja (mamy w architekturze → priorytet #1 Phase 2)
5. **"Anbefalt handling"** przy każdym werdykcie (jurist: ustalenie bez zalecenia to pół pracy)
6. **Alerty wygasania umów + wykorzystanie ramy %** (avtaleforvalter) → Phase 2
7. **Usługa raportowa** jako wejście dla małych jednostek (rådmann: "wyślijcie faktury, oddajcie raport — kupię jutro") → potwierdza model wejścia
8. **"Book 20-min gjennomgang"** — samoobsługowe demo bez następnego kroku = wyciek leadów

Odrzucone z zasadą: udawane moduły (Visma/SAP-przyciski bez backendu), testimoniale/fabrykowany
social proof. W produkcie compliance fałszywa śrubka unieważnia całą maszynę.

Kandydaci Phase 2 (decyzja na bramce 21.07, z danymi z ankiety/rozmów):
reglement-warstwa (persona: kommune-rådgiver) · alerty umów (avtaleforvalter) · raport zbiorczy PDF
(revisor) · tygodniowy digest mailowy (verkstedleder) · SSO/Entra (IT-sjef) · widok dostawcy (leverandør).

## 4. Decyzje HQ

- Zakres naprawy: WYŁĄCZNIE inscenizacja + 4 tanie dodatki (sekcja 5). Zamrożenie zakresu obowiązuje.
- Mapa platformy ("Plattformen") z uczciwymi badge'ami: Tilgjengelig / Under utvikling / Roadmap —
  pokazuje wizję bez budowania; SpareParts AI linkowany jako żywy moduł ekosystemu.
- Bramka 21.07 decyduje o kolejności Phase 2 — nie recenzje, nie nerwy.

## 5. IMPLEMENTATION BRIEF — paste to Claude Code (English, repo convention)

Partner directive (2026-07-10): demo re-staging after buyer-perspective audit. NO new engine
features except where explicitly listed. Core/ untouched except one CSV helper if needed at UI level.
All UI texts Norwegian (bokmål). Definition of DONE applies to every task. Work in this order:

**T1 — Hjem = result-first hero.**
Replace the four descriptive cards as the opening with:
(a) headline + value line: "Anskaffelsessjekk" / "Kontroll av fakturaer mot rammeavtaler,
e-postavtaler og regelverket 2026 — med full sporbarhet.";
(b) a live example card rendered from the actual engine (invoice F-1003): show verdict badge
(TIL VURDERING, yellow), one-line story: "Prisen avvek fra rammeavtalen — systemet fant
e-postavtalen fra 12. juni (J. Hansen). Krever formalisering." and a primary button
"Se hele analysen →" that navigates to Fakturakontroll with F-1003 preselected and the check
auto-run (use st.session_state + st.switch_page);
(c) a hero metric: "Verdi funnet i demoporteføljen: <computed from engine> kr";
(d) keep the SYNTETISKE DATA banner but visually secondary (st.caption-level under the hero);
(e) the four module cards move below the fold, one line each.

**T2 — Fakturakontroll = audit card, not a log.**
When arriving from Hjem (session flag) preselect F-1003 and run the check automatically.
Render the verdict as a large colored block (st.error/st.warning/st.success) with the amount:
"AVVIK — 12 000 kr over avtalt" pattern. Under it findings as cards; the grunnlag line for
EMAIL-source commitments gets a gold left border and prefix "📧 E-postavtale:". Add to every
finding an "Anbefalt handling" line derived from code: PRICE_ABOVE_AGREED → "Krev kreditnota
eller avklar prisgrunnlag med leverandør"; QTY_ABOVE_MAX → "Avklar mermengde mot avrop";
INFORMAL_BASIS → "Formaliser e-postavtalen med tillegg/anneks"; MISSING_RECEIPT → "Bekreft mottak
før betaling"; MISSING_ORDER → "Knytt faktura til bestilling/avrop"; NO_AGREED_BASIS →
"Etabler avtalegrunnlag eller vurder enkeltkjøp". Mapping lives in the UI layer (dict in page or
app/texts.py) — do NOT modify core. The PDF download button becomes primary
("Last ned protokoll (PDF)", type="primary"), and next to it a link-button
"Book 20-min gjennomgang" → mailto:asliwa1986@gmail.com?subject=Anskaffelsessjekk%20gjennomgang.

**T3 — Avtaler og forpliktelser: make the differentiator visible.**
E-mail commitments render in a visually distinct block: gold left border (#B08D2E), header
"📧 E-postavtaler i kontrollgrunnlaget — unikt for Anskaffelsessjekk", status chips for
formalization. Contract lines stay as-is.

**T4 — Terskelsjekk: visual path.**
Render the result as three visual steps with arrows (three st.columns with bordered containers):
"1. Regime: FOSA → 2. Terskel: over/under X kr → 3. Konsekvens: PROTOKOLLPLIKT (§...)". Keep the
existing citation expanders under it. Add caption: "Regimet vurderes ALLTID før beløpet — beløp
avgjør aldri regime."

**T5 — Styringsinformasjon: controller view.**
Verdi funnet becomes the hero metric (large, first, gold accent). Add a download button
"Eksporter funn (CSV)" exporting one row per finding across all invoices (invoice_number,
supplier, code, severity, message, expected, actual, deviation_amount, citation) — build the CSV
at UI level from existing check results (pandas is available via streamlit). Add per-supplier
deviation split (simple table or bar).

**T6 — New page: app/pages/5_Sikkerhet.py "Sikkerhet og databehandling".**
Static Norwegian content, sober tone: synthetic-data-only demo; append-only audit trail with rules
version; secrets via environment variables, never in code; architecture is containerizable —
on-prem deployment possible by design (relevant for forsvarssektoren); planned for production:
data residency in Norway/EEA, DPIA before processing real e-mail data (e-mails contain personal
data — data minimization principle), SSO (Entra ID) on the roadmap. Footer disclaimer as elsewhere.

**T7 — Institutional chrome on every page.**
Navy (#1F3A5F) header band with product name (thin, HTML block), consistent footer:
"Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og innkjøp ·
kontakt: asliwa1986@gmail.com · Syntetiske data". Reduce empty whitespace on Hjem
(layout="centered" stays).

**T8 — Contract update.** Add to CLAUDE.md Current tasks a note that T1–T7 supersede previous
polish tasks; Definition of DONE (a–e) applies; after completion append STATUS.md entry and push.
Verify on the live Streamlit Cloud URL after push (auto-redeploy) — open every page including the
new Sikkerhet page and download both PDF and CSV.

## 6. Kryterium odbioru (dla HQ)

Test 8 sekund: wejście na Hjem → czy w 8 s widzę wynik, kwotę i przycisk "pokaż mi"?
Test 2 minut: ścieżka Hjem → analiza F-1003 → PDF → dashboard → CSV bez zgadywania, co kliknąć.
Test zaufania: stopka z człowiekiem + strona Sikkerhet istnieją.
