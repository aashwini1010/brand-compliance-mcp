# Myridius Brand Design System — Website & Portal Guide
*A reference for AI software development tools (v0, Cursor, Bolt, Lovable, Claude Code, etc.) to build a website/portal in this brand.*

---

## 1. Brand Identity

| Attribute | Value |
|---|---|
| **Brand name** | myridius (lowercase wordmark, camel-case in prose) |
| **Voice** | Confident, calm, expert, human. Plain language with technical authority. Never hype-y, never salesy. |
| **Personality** | Modern, sophisticated, quietly innovative, trustworthy, accessible to non-experts. |
| **Logo** | Stylized triple-wave "M" mark in mint-green (`#52E081`) paired with lowercase sans-serif wordmark "myridius" in dark slate (`#0C2226` or `#194247`). Optional ™ superscript. |
| **Logo placement** | Always **bottom-left** in headers, footers, panels. Never centered, never inline with body copy. |

---

## 2. Color Palette

Use CSS variables. Primary canvas is **light** (`Base Linen`). Dark surfaces appear in **section dividers, hero areas, callouts, modals**.

### 2.1 Core Tokens

| Token | Hex | RGB | HSL | Use |
|---|---|---|---|---|
| `--cloud-white` | `#FFFFFF` | `255 255 255` | `0 0% 100%` | Pure white surface |
| `--base-linen` | `#F6F3F0` | `246 243 240` | `30 23% 95%` | **Primary light background** (off-white, warm) |
| `--carbon-moss` | `#0C2226` | `12 34 38` | `187 60% 10%` | **Primary dark background** (near-black teal) |
| `--quantum-leaf` | `#194247` | `25 66 71` | `187 46% 19%` | Primary text on light, dark teal surface |
| `--virtual-tide` | `#09A78D` | `9 167 141` | `169 90% 35%` | Primary brand accent (CTA buttons, links, focus rings) |
| `--digital-pavo` | `#337077` | `51 112 119` | `188 39% 33%` | Secondary brand accent (subtler teal) |
| `--pulse-green` | `#52E081` | `82 224 129` | `140 68% 60%` | Logo mark, decorative highlights (NEVER for body text) |
| `--neural-beam` | `#E5FD84` | `229 253 132` | `76 97% 75%` | Lime-yellow accent (highlights, hand-drawn annotations, NEVER for body text on white) |

### 2.2 Dark Mode Accent Palette

When surface is `--carbon-moss` (`#0C2226`):

| Token | Hex | Use |
|---|---|---|
| `--dm-text-cloud` | `#FFFFFF` | Primary text |
| `--dm-text-linen` | `#F6F3F0` | Primary text (preferred) |
| `--dm-accent-pulse` | `#52E081` | Accent text/UI only |
| `--dm-accent-beam` | `#E5FD84` | Accent text/UI only |
| `--dm-accent-tide` | `#09A78D` | Accent text/UI only |
| `--dm-accent-pavo` | `#337077` | Accent text/UI only |

### 2.3 Light Mode Accent Palette

When surface is `--base-linen` (`#F6F3F0`) or `--cloud-white`:

| Token | Hex | Use |
|---|---|---|
| `--lm-text-moss` | `#0C2226` | Primary text (Carbon Moss) |
| `--lm-text-leaf` | `#194247` | Primary text (Quantum Leaf, softer) |
| `--lm-accent-tide` | `#09A78D` | Accent only — links, buttons, icons |
| `--lm-accent-pavo` | `#337077` | Accent only |

### 2.4 Chart & Data-Vis Palette

For graphs, tables, dashboards (ordered):

`#52E081` → `#337077` → `#09A78D` → `#94DEA5` → `#CBEBBD` → `#DBF4D0` → `#285C62` → `#163439` → `#E5FD84` → `#10B18E`

### 2.5 Accessibility Rules (HARD)

- **NEVER** use `--pulse-green` (`#52E081`) or `--neural-beam` (`#E5FD84`) as body text on `--base-linen` or `--cloud-white` — fails WCAG AA. Use them only on dark surfaces or as decorative fills, icons, charts.
- Body text minimum contrast ratio: **4.5:1** against its surface.
- Always run a contrast check before selecting text color.

---

## 3. Typography — Montserrat

**Single typeface family for the entire product.** This replaces whatever the original deck used.

### 3.1 Font Stack

```css
--font-sans: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
@import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,600&display=swap");
```

### 3.2 Scale (rem-based, fluid via clamp)

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `--fs-display` | `clamp(3rem, 6vw + 1rem, 6rem)` | 800 | 1.05 | -0.02em | Hero headline (single short phrase) |
| `--fs-h1` | `clamp(2.25rem, 4vw + 1rem, 4rem)` | 700 | 1.1 | -0.015em | Section title |
| `--fs-h2` | `clamp(1.75rem, 2.5vw + 0.75rem, 2.75rem)` | 700 | 1.15 | -0.01em | Sub-section title |
| `--fs-h3` | `clamp(1.375rem, 1.5vw + 0.5rem, 1.875rem)` | 600 | 1.25 | -0.005em | Card / column heading |
| `--fs-h4` | `1.25rem` | 600 | 1.3 | 0 | Small heading / sub-card |
| `--fs-body-lg` | `1.125rem` | 400 | 1.6 | 0 | Lead paragraph |
| `--fs-body` | `1rem` | 400 | 1.6 | 0 | Body copy |
| `--fs-body-sm` | `0.9375rem` (15px) | 400 | 1.55 | 0 | Secondary copy, helper text |
| `--fs-caption` | `0.8125rem` (13px) | 500 | 1.45 | +0.04em | All-caps small labels |
| `--fs-overline` | `0.75rem` (12px) | 600 | 1.4 | +0.12em | Eyebrow text, kicker, breadcrumb |
| `--fs-button` | `0.9375rem` | 600 | 1 | +0.02em | CTA buttons |
| `--fs-italic` | inherit | 400 italic | inherit | inherit | Pull-quote, attribution, decorative |

### 3.3 Style Rules

- **Headlines**: Bold (700+), tight line-height (1.05–1.15), slightly negative letter-spacing.
- **Eyebrow labels**: ALL CAPS, weight 600, letter-spacing +0.08em to +0.12em, color `--virtual-tide` on light OR `--pulse-green` on dark.
- **Body copy**: Regular (400), line-height 1.6, neutral slate color (`--quantum-leaf` on light, `--base-linen` on dark).
- **Italic in display rules**: Use italic Montserrat (400 italic) for editorial pull-quotes and signature accents — e.g. *"The Competitive Edge"*.
- **No other font families.** No serifs, no mono, no display fonts. Ever.

---

## 4. Spacing & Grid

### 4.1 Spacing Scale (8pt base)

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 24px;
--space-6: 32px;
--space-7: 48px;
--space-8: 64px;
--space-9: 96px;
--space-10: 128px;
--space-11: 160px;
/* Section vertical rhythm */
--section-py: clamp(64px, 8vw, 128px);
```

### 4.2 Layout Grid

- **Page max-width**: `1280px`, with `max-width: 1440px` for marketing hero sections.
- **Container padding**: `clamp(20px, 4vw, 56px)` left/right.
- **Column system**: 12-column grid, `gap: 32px` on desktop, `16px` on mobile.
- **Common splits**: 50/50, 40/60 (text-block-heavy slides), 30/70 (photo-left hero).
- **Vertical rhythm**: 48–96px between major sections; 24–32px between sub-elements.

### 4.3 Border Radius

```css
--radius-sm: 6px;
--radius-md: 12px;
--radius-lg: 20px;
--radius-pill: 999px;
```

Card radius: `12–20px`. Button radius: `999px` (pill) by default — or `8px` for square buttons. Input fields: `8–12px`.

---

## 5. Logo Usage

| Rule | Do | Don't |
|---|---|---|
| Placement | Bottom-left corner of page/panel. Footer-left in long pages. | Center, right-aligned, inline with body copy |
| Color on light surfaces | `--quantum-leaf` wordmark + `--pulse-green` icon | Any color other than the two above |
| Color on dark surfaces | `--base-linen` wordmark + `--pulse-green` icon | Pure white wordmark — prefer linen for warmth |
| Background | Transparent background only | Color background, gradient background, busy imagery directly behind logo |
| Clear space | At least 1× the icon height on all sides | Cramped next to text or image edges |
| Sizing | Logo height ≥ 24px, ≤ 48px in body; up to 64px in hero | Tiny (under 20px) or oversized |
| Modifications | Never recolor, outline, rotate, skew, or modify | Stretch, add effects, swap icon for emoji, replace with text |

If logo asset is unavailable, render a **placeholder mark**: a circular green badge with `M` in italic Montserrat weight 600, paired with `myridius™` wordmark.

---

## 6. Signatures — What Makes the Brand Recognisable

These three elements appear in nearly every slide. Web versions of them are mandatory for visual coherence:

### 6.1 Organic Wave Graphic (right-margin ornament)

Fluid, asymmetric, vector shape hugging the right edge of section dividers and section transitions. Composition rules:

- 100–300 flowing parallel curves, hairline weight (0.75–1.5px), color `--virtual-tide` at 30–60% opacity.
- Curves originate from bottom-right corner, fan upward and outward, leaving white/linen space on the inside.
- On dark surfaces, use `--pulse-green` or `--neural-beam` at low opacity.
- Always decorative — never carry informational content.
- Sizing: takes up **30–50% of viewport width** at section dividers; smaller (10–20%) as decorative bands in lighter sections.

### 6.2 Hand-drawn Editorial Annotations

Tiny informal notes in bright lime/yellow (`--neural-beam`), with a small curved arrow. These are an internal-template marker — use them on docs, onboarding overlays, empty-state illustrations, and tutorial/walkthroughs.

```html
<!-- Pattern -->
<span style="font-family:'Caveat', cursive; color:#E5FD84; font-size:14px;">
  Try clicking the chart below
  <svg>arrow</svg>
</span>
```

Note: in shipped product UI, replace with proper UI labels — the `Caveat` handwriting only appears in **developer docs, internal templates, and template-builder UIs**, never customer-facing marketing.

### 6.3 Gradient "Fade-Background" Cards

Cards on dark surfaces that **fade to transparent on the right edge** — they appear to float out of the background. Implement as:

```css
.gradient-card {
  background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 60%, transparent 100%);
  border: 1px solid rgba(82, 224, 129, 0.15);
  border-radius: 12px;
}
```

Use for: info callouts, stat blocks, content cards on dark hero sections.

---

## 7. Components

### 7.1 Buttons

| Variant | Background | Text | Border | Hover | Use |
|---|---|---|---|---|---|
| **Primary (CTA)** | `--virtual-tide` | `--cloud-white` | none | darken 8%, lift `translateY(-1px)`, shadow `0 8px 24px rgba(9,167,141,0.25)` | Primary action |
| **Secondary** | transparent | `--quantum-leaf` (on light) / `--base-linen` (on dark) | `1.5px solid currentColor` | fill with tint at 10% opacity | Secondary action |
| **Tertiary / Ghost** | transparent | `--virtual-tide` | none | underline grows | Low-emphasis link |
| **Icon button** | transparent | current | none | background tint | Header actions |

- **Shape**: pill (`--radius-pill`) by default; rectangular with `8px` radius only in dense data tables.
- **Padding**: `12px 28px` (medium); `16px 36px` (large); `8px 16px` (small).
- **Font**: Montserrat 600, `--fs-button`, +0.02em letter-spacing.
- **Destructive variant**: background `#C84B47`, text `#FFFFFF`.
- **Disabled**: `opacity: 0.5; cursor: not-allowed; pointer-events: none`.
- **Always** include focus ring: `outline: 2px solid --virtual-tide; outline-offset: 2px`.

### 7.2 Cards

Two main patterns:

**(a) Light surface card** (on `--base-linen` page):

```css
background: #FFFFFF;
border: 1px solid rgba(25, 66, 71, 0.08);
border-radius: 12px;
padding: 32px;
box-shadow: 0 1px 3px rgba(12, 34, 38, 0.04);
```

**(b) Dark surface gradient card** (on `--carbon-moss` section):

```css
background: linear-gradient(135deg, rgba(82,224,129,0.06) 0%, rgba(9,167,141,0.02) 50%, transparent 100%);
border: 1px solid rgba(82, 224, 129, 0.12);
border-radius: 20px;
padding: 40px;
```

Cards may carry a **color-coded header strip** (8px tall top bar in sequence: `--pulse-green` → `--virtual-tide` → `--digital-pavo` → `--neural-beam`) when they represent process steps, tiers, or categories.

### 7.3 Forms & Inputs

- Background: `--cloud-white`, border `1px solid rgba(25,66,71,0.16)`.
- Border radius: `12px` (modern) or `8px` (compact).
- Padding: 14px vertical, 16px horizontal.
- Focus state: border becomes `2px solid --virtual-tide`, ring `0 0 0 4px rgba(9,167,141,0.15)`.
- Label: Montserrat 600, 14px, color `--quantum-leaf`, sits above input.
- Helper text: Montserrat 400, 13px, color `--digital-pavo`.

### 7.4 Navigation

**Top nav on light backgrounds:**

```css
background: rgba(246, 243, 240, 0.85);
backdrop-filter: saturate(140%) blur(12px);
border-bottom: 1px solid rgba(25,66,71,0.08);
height: 72px;
```

- Logomark left (logo, not full wordmark).
- Links centered or right-aligned, Montserrat 500 15px.
- Active link: 2px underline `--virtual-tide`, 4px below text.
- CTA on the far right: `--virtual-tide` pill button.

**Side nav for portal/dashboard pages:**

- Width: `260px` (collapsed: `72px`).
- Background: `--carbon-moss`.
- Link color: `--base-linen`.
- Active link: 4px left bar in `--pulse-green`, surface gets `rgba(82,224,129,0.06)` tint.
- Icons: 20px, stroke-style or flat, paired with label.

### 7.5 Hero Iconography

Two icon-container styles:

**(a) Filled circle (services / features):**

```css
width: 64px; height: 64px; border-radius: 50%;
background: #52E081;            /* light page */
color: #0C2226;                 /* icon stroke */
display: grid; place-items: center;
```

**(b) Outline circle (cards on light):**

```css
width: 56px; height: 56px; border-radius: 50%;
background: #0C2226;
color: #52E081;
border: 1px solid #52E081;
```

Icons always 1.5–2px stroke, geometric, **no emoji**, **no icons with multi-color fills** beyond the brand palette.

### 7.6 Stats / Numbers

Display numbers in Montserrat **800 weight**, `--fs-display` for hero metrics, `--fs-h1` on detail pages. Color: `--virtual-tide` on light, `--pulse-green` on dark. Always supply unit (`Trillion`, `Million`) directly below in all-caps `--fs-overline`.

### 7.7 Charts

- Use the chart palette in section 2.4.
- Always start the value legend (1.3, 85, 380) with the **first number in the brand-accent color**; subsequent numbers in monochrome variants of `--quantum-leaf`.
- Bar charts: 4–8px corner radius on bars. Line charts: 2.5px stroke, dotted gridlines `rgba(25,66,71,0.08)`.
- Tooltip: `--carbon-moss` background, `--base-linen` text, 8px radius.

### 7.8 Photo Treatment

- **Always** use authentic, warm-toned, real-people photography.
- **NEVER** stock-clipart, posed studio shots, AI-generated faces.
- Default photo treatment: subtle desaturation (-10%), color graded toward the brand teal range.
- Photo overlays: 40–60% `--carbon-moss` gradient from bottom to allow white text on top.
- Aspect ratios: 4:5 (portrait, photo-left), 16:9 (hero), 3:2 (cards).

---

## 8. Layout Patterns

### 8.1 Page Structure

```
[Top Nav 72px — light, blur, semi-transparent]
[Hero Section — 100vh on landing, 60vh on inner — light OR dark]
[Content Section 1 — light, generous padding]
[Content Section 2 — light]
[Dark Section — Carbon Moss surface — for visual contrast]
[Content Section 3 — light, complex grid]
[Footer — Carbon Moss, logo + columns + legal]
```

**Rule:** alternate light/dark sections for visual rhythm. Never two dark sections in a row. Never two sections of identical composition.

### 8.2 Hero Compositions (5 patterns)

1. **Light hero, text-left, wave-right** — most common. Headline + sub + 2 CTAs in left 50%. Wave ornament + product screenshot or stock image in right 50%.
2. **Dark hero, photo-top** — full-width lifestyle photo top 40%, dark section below with headline + CTAs.
3. **Dark hero, photo-left** — vertical full-bleed photo left 30%, dark surface right 70% with text.
4. **Dark hero with radial bar chart** — dark surface, headline top-left, decorative ring chart bottom-right.
5. **Section-divider-style** — full-bleed dark teal background with single bold sentence left-aligned, wave ornament right.

### 8.3 Content Sections

- **Three-column feature grid** (most-used). Column heading + icon-container + 2-3 line body. All columns equal width 1fr; gap 32px.
- **Four-column process steps**. Each card numbered 01–04 in colored top-strip; bold title; supporting copy.
- **Stat row** — three to four large numbers with unit and one-line context. Used at top of overview pages.
- **Two-column comparison** — 60% content left, 40% visual right; or 40/60 reversed.
- **Carousel / logo wall** — single row of partner/customer logos, grayscale by default, full-color on hover.

### 8.4 Spacing discipline

- 96px between major page sections on desktop, 64px on mobile.
- 48px between sub-blocks within a section.
- 24px between heading group and body.
- 16px between heading and eyebrow.
- Body paragraphs max-width: `65ch`.

---

## 9. Voice & Copy

- **Active voice.** "We help you ship faster" not "Faster shipping is enabled by our platform."
- **Plain over clever.** Skip "synergize", "leverage", "delve".
- **Confident without hype.** "Trusted by 380M+ users" is fine. "The world's #1 most amazing platform" is not.
- **Format eyebrows as ALL CAPS short labels** (3–5 words max), followed by sentence-case headline.
- **Sentence case in headlines** (only first word capitalized, except proper nouns).
- **CTA copy is action-oriented:** "View case study" / "Book a demo" / "Get started" / "Explore platform". Avoid "Submit" and "Click here".

---

## 10. Do's & Don'ts (Hard Rules)

| ✓ Do | ✗ Don't |
|---|---|
| Use Montserrat exclusively | Mix in Poppins, Inter, serif, or display fonts |
| Default surface is `--base-linen` | Make the entire site dark |
| Alternate light / dark sections | Stack 3+ dark sections in a row |
| Place logo bottom-left | Center logo or put it next to nav links |
| Use the wave ornament on dividers | Add gradients, glows, or glassmorphism |
| Use `--virtual-tide` for accent only | Color body text in pulses/lime yellow on light |
| Use 1.5–2px stroke icons | Use filled multicolor emoji icons |
| Hand-drawn annotations in template docs only | Leave them in shipped product UI |
| Use authentic photography | Use AI-generated faces or stock clipart |
| Maintain 4.5:1 text contrast | Sacrifice accessibility for color expressiveness |

---

## 11. Master AI Builder Prompt (Copy-Paste Ready)

Paste the block below verbatim into v0 / Cursor / Bolt / Lovable / Claude Code when generating the site:

````
Build a website/portal in the **Myridius** brand system. Follow this spec exactly.

## Brand
- Brand name: **myridius**
- Voice: confident, calm, expert, human. Plain language, no hype.
- Logo: stylized wave "M" in mint-green (#52E081) + lowercase Montserrat wordmark. Always bottom-left.

## Typography
- **Single typeface: Montserrat** — bold for headlines, regular for body.
- Display: clamp(3rem, 6vw+1rem, 6rem), weight 800, line-height 1.05, letter-spacing -0.02em.
- H1: clamp(2.25rem, 4vw+1rem, 4rem), weight 700.
- Body: 1rem / 1.6, weight 400.
- Eyebrow / overline: ALL CAPS, weight 600, letter-spacing +0.10em.
- Pull-quotes: italic Montserrat.
- No other font families.

## Color palette (CSS variables)
Light surface (default page):
  --cloud-white: #FFFFFF
  --base-linen: #F6F3F0   ← PRIMARY background
  --quantum-leaf: #194247  ← primary text
  --virtual-tide: #09A78D  ← primary accent, CTA, links
  --digital-pavo: #337077  ← secondary accent
  --pulse-green: #52E081   ← logo, decorative only
  --neural-beam: #E5FD84   ← decorative highlights only
Dark surface (alternating sections):
  --carbon-moss: #0C2226   ← PRIMARY dark background (text: #F6F3F0, accent: #52E081 / #09A78D)
Chart colors in order: #52E081, #337077, #09A78D, #94DEA5, #CBEBBD, #DBF4D0, #285C62, #163439, #E5FD84, #10B18E.

## Background policy
- Primary surfaces = LIGHT (--base-linen or --cloud-white). Most pages should feel airy.
- Dark surfaces (--carbon-moss) appear in: hero sections, section dividers, modals, footer, dashboards.
- Alternate light/dark sections rhythmically. Never two dark sections back-to-back.

## Layout principles
- 8pt spacing scale. Page max-width 1280px. 12-column grid, 32px gap.
- Section vertical padding 96–128px on desktop.
- Generous whitespace. Asymmetric layouts allowed.
- Container padding clamp(20px, 4vw, 56px).
- Body paragraphs max-width 65ch.

## Signature elements (mandatory)
1. **Organic wave ornament** — flowing parallel curves on right edge of dividers/heroes. Color #09A78D at 30–60% opacity, hairline stroke 0.75–1.5px. Decorative only.
2. **Logo placement** — always bottom-left.
3. **Hand-drawn annotations** (in template/docs/empty states only, never in shipped marketing UI) — Caveat handwriting font, color #E5FD84, with curved arrow, leading to a labeled element.
4. **Gradient fade-cards on dark sections** — cards that fade to transparent on the right, appearing to float out of the background.

## Components
Buttons (pill --radius-pill 999px or rectangular 8px):
  Primary: bg #09A78D, text #FFFFFF. Hover: darken 8%, lift, soft shadow.
  Secondary: transparent bg, 1.5px border in currentColor.
  Ghost / tertiary: transparent, link-colored, underline on hover.
  All buttons: focus ring 2px solid #09A78D with 4px offset. Always include focus state.

Cards:
  On light: white bg, 1px subtle border (#194247 at 8% opacity), radius 12px, shadow 0 1px 3px rgba(12,34,38,0.04).
  On dark: gradient fade-card (light tint to transparent), border #52E081 at 12% opacity, radius 20px.

Forms:
  Inputs white, border 1px solid rgba(25,66,71,0.16), radius 12px.
  Focus border becomes 2px solid #09A78D with 4px outer glow.

Icons:
  Geometric, 1.5–2px stroke. Single brand color (--pulse-green or --quantum-leaf). NEVER emoji.

Navigation:
  Light surface top nav (72px, semi-transparent linen with backdrop-blur).
  Dashboard side nav (260px, --carbon-moss surface) for portal pages.

Charts:
  Use the chart palette in order. 4–8px corner radius on bars. Dotted gridlines. Tooltip on --carbon-moss.

## Imagery
- Authentic, real-people photography. Warm color grade.
- Always desaturate -10% to push toward brand teal range.
- Aspect ratios: 4:5 (portrait), 16:9 (hero), 3:2 (cards).
- Dark gradient overlays (45% --carbon-moss) on photos for white text legibility.

## Page structure (default)
1. Top nav (light, blur)
2. Hero — light or dark, with wave ornament
3. Light content section (3-col feature grid or stat row)
4. Light content section (deep-dive / 4-step process cards)
5. Dark section (testimonial / case study / CTA)
6. Light content section (pricing or services)
7. Footer (dark, logo bottom-left + columns + legal)

## Hard rules (NEVER violate)
- Only Montserrat. Never Poppins, Inter, serif, or display fonts.
- Never use --pulse-green or --neural-beam as body text on light surfaces.
- Always logo bottom-left.
- Always include focus states on interactive elements.
- Body text contrast ratio ≥ 4.5:1.
- No emoji as UI icons. No AI-generated faces. No clipart.
- Wave ornament is decorative — never carries information.
- Keep annotations out of shipped marketing UI.

Build the [page/portal/landing] now. Output a self-contained HTML/CSS/JS file with the design system in :root CSS variables and semantic HTML.
````

---

## 12. One-line Summary

**Myridius** = light-primary, Montserrat-only, signal-teal `(#09A78D)` accent, mint-green logo, asymmetric white space, organic wave ornament, confident-and-calm voice.
