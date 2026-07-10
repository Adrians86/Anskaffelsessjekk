# SpareParts AI — Setup & Troubleshooting

## Kontekst dla czatu / AI
Projekt to aplikacja webowa SpareParts AI do zarządzania zapasami części zamiennych, analizy danych oraz obliczeń ROP. Została zbudowana na Next.js 14 + TypeScript + Supabase, z logowaniem, wieloma organizacjami (multi-tenant) i importem danych z plików Excel/MB51/MB52.

Co już zrobiliśmy:
- setup autoryzacji: sign up / sign in / logout,
- tworzenie organizacji i profilu podczas rejestracji,
- middleware i ochrona dashboardu,
- dashboard z KPI oraz strony upload i ROP,
- parser importu danych i prosty silnik ROP.

Aktualny cel: uruchomić aplikację lokalnie, skonfigurować Supabase i zweryfikować pełny flow end-to-end.

## Struktura która MUSI istnieć w `D:\ASNorth\spareparts-web\`

```
spareparts-web/
├── .env.local                              ← z Twoim ANON KEY
├── src/
│   ├── middleware.ts                       ← NOWE
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx                        ← NOWE (redirect)
│   │   ├── login/
│   │   │   └── page.tsx                    ← NOWE
│   │   ├── dashboard/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── upload/page.tsx
│   │   │   └── rop/page.tsx
│   │   └── api/
│   │       ├── setup-org/route.ts          ← NOWE
│   │       ├── import/route.ts
│   │       └── rop/route.ts
│   └── lib/
│       ├── types.ts
│       ├── rop-engine.ts
│       ├── file-parser.ts
│       └── supabase/
│           ├── client.ts
│           └── server.ts
```

## Krok 1 — Supabase SQL (dwa pliki, kolejność)

W Supabase → **SQL Editor** → **New Query**:

**Pierwszy raz:** wklej i uruchom `supabase_schema.sql`
**Potem:** wklej i uruchom `supabase_schema_patch_v2.sql` (fix dla signup)

## Krok 2 — Supabase Auth: włącz email

Supabase → **Authentication** → **Providers** → **Email** → sprawdź czy jest ON.

Opcjonalnie wyłącz "Confirm email" (Authentication → Settings → **Email Confirmations** → OFF) na czas developmentu, żeby signup od razu logował.

## Krok 3 — .env.local

Otwórz `spareparts-web/.env.local` w VS Code:

```
NEXT_PUBLIC_SUPABASE_URL=https://hikqtgkngqrokhceaefl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
```

**Gdzie znaleźć anon key:** Supabase → **Settings** → **API** → `anon` `public` (długi string zaczynający się od `eyJ...`)

## Krok 4 — Instalacja bibliotek

```powershell
cd D:\ASNorth\spareparts-web
npm install @supabase/supabase-js @supabase/ssr lucide-react xlsx
```

## Krok 5 — Uruchom

```powershell
npm run dev
```

Otwórz: **http://localhost:3000**

Powinno przekierować do `/login`. Kliknij zakładkę **Sign Up**, wpisz email + hasło + nazwę organizacji → utworzy konto i przekieruje na `/dashboard`.

---

## Troubleshooting — najczęstsze problemy

### "Module not found: @supabase/ssr"
```powershell
npm install @supabase/ssr @supabase/supabase-js
```

### Po signup: "Failed to create organization"
Nie uruchomiłeś `supabase_schema_patch_v2.sql`. Uruchom go teraz.

### Po signup: "Email not confirmed"
Wyłącz email confirmation w Supabase → Authentication → Settings.

### `/dashboard` przekierowuje na `/login` ciągle
Sprawdź czy plik `src/middleware.ts` jest w folderze `src/` a NIE w `src/app/`.

### Import pliku wyrzuca błąd 401
Zaloguj się najpierw, potem próbuj upload.

### Import pliku wyrzuca błąd 500
Otwórz DevTools (F12) → Console → wklej mi treść błędu.

### Localhost pokazuje białą stronę
1. Ctrl+C w PowerShell (zatrzymaj serwer)
2. W Eksploratorze usuń folder `.next`
3. `npm run dev` ponownie

---

## Co działa po tym setupie

- Landing → auto-redirect (login lub dashboard)
- Sign up: nowe konto + organizacja + profil w jednym kroku
- Sign in: istniejące konto
- Multi-tenant: dane każdej organizacji są izolowane (RLS)
- Dashboard z KPI cards
- Upload MB51/MB52 z AI column mapping
- ROP results z filtrowaniem i eksportem CSV

## Co jest TODO (kolejne kroki)

1. Strony: Stock, Aging, ABC, Anomalies, Promotions, Audit, Settings
2. Language switcher (EN/NO/PL) w UI Next.js
3. Deploy na Netlify z domeną spareparts.asnorth.no
4. Compliance & Procurement Verification AI (osobny moduł, po SpareParts)

Napisz w którym kroku się zatrzymujesz albo jaki dokładnie błąd widzisz — wtedy wiem co naprawić.
