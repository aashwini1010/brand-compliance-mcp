# Brand compliance report

**Run:** `run-20261011-050426-d673ec`  ·  **Status:** completed

|  |  |
|---|---|
| Brand guide | myridius-brand-guide.md |
| Artifact | sample-marketing-email.html (email) |
| Original file | unchanged |
| Fingerprint (sha256) | 6e4da8d77a0bdcdb05d37fa65809c283792139c76712d16d5ce5d198d2b74c3e |
| Started | 2026-10-11T05:04:26+00:00 |

Why it was treated as email:

- email +3: 3 layout table(s)
- email +1: nested tables
- email +3: Outlook (MSO) conditional comments
- email +2: Microsoft Office XML namespaces
- email +2: email-client meta tag
- email +2: mso-* CSS properties
- email +1: legacy bgcolor/valign attributes
- email +2: 22 of 39 elements carry inline styles
- email +1: hidden preheader text

## Summary

| Rules | Count |
|---|---|
| Applied | 25 |
| Understood but not applied | 170 |
| Could not interpret | 95 |
| Conflict (unresolved) | 4 |
| Reference definition | 35 |
| **Total rules** | 329 |

Changes made: **45**  ·  changes rolled back: **0**  ·  contradictions in the guide: **3**

## Verification

- **contrast**: pass
  - 11 text element(s) checked against 4.5:1
  - 0 could not be checked (background or colour unknown)
  - 1 already failed before any change (not caused by this tool)
  - 0 change(s) caused a failure
- **forbidden-color**: pass
  - 2 colour ban(s) checked, 0 violation(s)
- **structure**: pass
  - 46 nodes identical, in the same order
- **assets**: pass
  - 4 asset reference(s) preserved, anchors intact
- **original-intact**: pass
  - source unchanged (sha256 6e4da8d77a0b...)
- **idempotence**: pass
  - a second run gives identical output

## 1. Rules applied

| Rule | What the guide says | Scope | Guide line | Result |
|---|---|---|---|---|
| R030 | Never use #52e081 as text.body colour on light surfaces | light | myridius-brand-guide.md:67 | Enforced by the forbidden-color check: 2 colour ban(s) checked, 0 violation(s) |
| R031 | Never use #e5fd84 as text.body colour on light surfaces | light | myridius-brand-guide.md:67 | Enforced by the forbidden-color check: 2 colour ban(s) checked, 0 violation(s) |
| R032 | text.body contrast must be at least 4.5:1 | all | myridius-brand-guide.md:68 | Enforced by the contrast check: 11 text element(s) checked against 4.5:1 |
| R035 | document font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif | all | myridius-brand-guide.md:80 | 8 change(s) made |
| R036 | @import: url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,600&display=swap") | all | myridius-brand-guide.md:81 | 1 change(s) made |
| R042 | heading.h1 font-weight: 700 | all | myridius-brand-guide.md:89 | 1 change(s) made |
| R043 | heading.h1 line-height: 1.1 | all | myridius-brand-guide.md:89 | 1 change(s) made |
| R044 | heading.h1 letter-spacing: -0.015em | all | myridius-brand-guide.md:89 | 1 change(s) made |
| R046 | heading.h2 font-weight: 700 | all | myridius-brand-guide.md:90 | 1 change(s) made |
| R047 | heading.h2 line-height: 1.15 | all | myridius-brand-guide.md:90 | 1 change(s) made |
| R048 | heading.h2 letter-spacing: -0.01em | all | myridius-brand-guide.md:90 | 1 change(s) made |
| R061 | text.body font-size: 1rem | all | myridius-brand-guide.md:94 | 3 change(s) made |
| R062 | text.body font-weight: 400 | all | myridius-brand-guide.md:94 | 5 change(s) made |
| R063 | text.body line-height: 1.6 | all | myridius-brand-guide.md:94 | 5 change(s) made |
| R064 | text.body letter-spacing: 0 | all | myridius-brand-guide.md:94 | 5 change(s) made |
| R077 | button.label font-size: 0.9375rem | all | myridius-brand-guide.md:98 | 1 change(s) made |
| R079 | button.label line-height: 1 | all | myridius-brand-guide.md:98 | 1 change(s) made |
| R093 | text.body color: #194247 | light | myridius-brand-guide.md:105 | 4 change(s) made |
| R094 | text.body color: #f6f3f0 | dark | myridius-brand-guide.md:105 | 1 change(s) made |
| R096 | Only the font Montserrat may be used | all | myridius-brand-guide.md:107 | Enforced through the font-family changes |
| R168 | button border-radius: 999px | all | myridius-brand-guide.md:223 | 1 change(s) made |
| R172 | button.label font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif | all | myridius-brand-guide.md:225 | 1 change(s) made |
| R173 | button.label font-weight: 600 | all | myridius-brand-guide.md:225 | 1 change(s) made |
| R174 | button.label letter-spacing: 0.02em | all | myridius-brand-guide.md:225 | 1 change(s) made |
| R276 | page.surface background: #f6f3f0 | all | myridius-brand-guide.md:391 | 1 change(s) made |

## 2. Change log

Every edit: which element, before and after, and the guideline behind it.

### R035 · document font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif (guide line myridius-brand-guide.md:80)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH003 | /html/body | font-family | (not set) | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH005 | /html/body/table/tr/td/table/tr[1]/td/p | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH010 | /html/body/table/tr/td/table/tr[2]/td/h1 | font-family | Georgia, "Times New Roman", serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH015 | /html/body/table/tr/td/table/tr[2]/td/p | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH019 | /html/body/table/tr/td/table/tr[4]/td/h2 | font-family | Georgia, "Times New Roman", serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH024 | /html/body/table/tr/td/table/tr[4]/td/p | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH035 | /html/body/table/tr/td/table/tr[6]/td/p[1] | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |
| CH041 | /html/body/table/tr/td/table/tr[6]/td/p[2] | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif |  |

### R036 · @import: url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,600&display=swap") (guide line myridius-brand-guide.md:81)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH001 | /html/head | @font-source | (not set) | https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,600&display=swap |  |

### R042 · heading.h1 font-weight: 700 (guide line myridius-brand-guide.md:89)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH011 | /html/body/table/tr/td/table/tr[2]/td/h1 | font-weight | (not set) | 700 |  |

### R043 · heading.h1 line-height: 1.1 (guide line myridius-brand-guide.md:89)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH013 | /html/body/table/tr/td/table/tr[2]/td/h1 | line-height | 36px | 1.1 | Overrides an inline style |

### R044 · heading.h1 letter-spacing: -0.015em (guide line myridius-brand-guide.md:89)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH012 | /html/body/table/tr/td/table/tr[2]/td/h1 | letter-spacing | (not set) | -0.015em | Outlook desktop ignores letter-spacing |

### R046 · heading.h2 font-weight: 700 (guide line myridius-brand-guide.md:90)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH020 | /html/body/table/tr/td/table/tr[4]/td/h2 | font-weight | (not set) | 700 |  |

### R047 · heading.h2 line-height: 1.15 (guide line myridius-brand-guide.md:90)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH022 | /html/body/table/tr/td/table/tr[4]/td/h2 | line-height | 28px | 1.15 | Overrides an inline style |

### R048 · heading.h2 letter-spacing: -0.01em (guide line myridius-brand-guide.md:90)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH021 | /html/body/table/tr/td/table/tr[4]/td/h2 | letter-spacing | (not set) | -0.01em | Outlook desktop ignores letter-spacing |

### R061 · text.body font-size: 1rem (guide line myridius-brand-guide.md:94)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH006 | /html/body/table/tr/td/table/tr[1]/td/p | font-size | 13px | 16px | rem converted to px (1rem = 16px); Overrides an inline style |
| CH036 | /html/body/table/tr/td/table/tr[6]/td/p[1] | font-size | 12px | 16px | rem converted to px (1rem = 16px); Overrides an inline style |
| CH042 | /html/body/table/tr/td/table/tr[6]/td/p[2] | font-size | 12px | 16px | rem converted to px (1rem = 16px); Overrides an inline style |

### R062 · text.body font-weight: 400 (guide line myridius-brand-guide.md:94)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH007 | /html/body/table/tr/td/table/tr[1]/td/p | font-weight | (not set) | 400 |  |
| CH016 | /html/body/table/tr/td/table/tr[2]/td/p | font-weight | (not set) | 400 |  |
| CH025 | /html/body/table/tr/td/table/tr[4]/td/p | font-weight | (not set) | 400 |  |
| CH037 | /html/body/table/tr/td/table/tr[6]/td/p[1] | font-weight | (not set) | 400 |  |
| CH043 | /html/body/table/tr/td/table/tr[6]/td/p[2] | font-weight | (not set) | 400 |  |

### R063 · text.body line-height: 1.6 (guide line myridius-brand-guide.md:94)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH009 | /html/body/table/tr/td/table/tr[1]/td/p | line-height | (not set) | 1.6 |  |
| CH018 | /html/body/table/tr/td/table/tr[2]/td/p | line-height | 24px | 1.6 | Overrides an inline style |
| CH027 | /html/body/table/tr/td/table/tr[4]/td/p | line-height | 24px | 1.6 | Overrides an inline style |
| CH039 | /html/body/table/tr/td/table/tr[6]/td/p[1] | line-height | 18px | 1.6 | Overrides an inline style |
| CH045 | /html/body/table/tr/td/table/tr[6]/td/p[2] | line-height | 18px | 1.6 | Overrides an inline style |

### R064 · text.body letter-spacing: 0 (guide line myridius-brand-guide.md:94)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH008 | /html/body/table/tr/td/table/tr[1]/td/p | letter-spacing | 1px | 0 | Outlook desktop ignores letter-spacing; Overrides an inline style |
| CH017 | /html/body/table/tr/td/table/tr[2]/td/p | letter-spacing | (not set) | 0 | Outlook desktop ignores letter-spacing |
| CH026 | /html/body/table/tr/td/table/tr[4]/td/p | letter-spacing | (not set) | 0 | Outlook desktop ignores letter-spacing |
| CH038 | /html/body/table/tr/td/table/tr[6]/td/p[1] | letter-spacing | (not set) | 0 | Outlook desktop ignores letter-spacing |
| CH044 | /html/body/table/tr/td/table/tr[6]/td/p[2] | letter-spacing | (not set) | 0 | Outlook desktop ignores letter-spacing |

### R077 · button.label font-size: 0.9375rem (guide line myridius-brand-guide.md:98)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH030 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | font-size | 16px | 15px | rem converted to px (1rem = 16px); Overrides an inline style |

### R079 · button.label line-height: 1 (guide line myridius-brand-guide.md:98)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH033 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | line-height | (not set) | 1 |  |

### R093 · text.body color: #194247 (guide line myridius-brand-guide.md:105)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH014 | /html/body/table/tr/td/table/tr[2]/td/p | color | #334e68 | #194247 | Overrides an inline style |
| CH023 | /html/body/table/tr/td/table/tr[4]/td/p | color | #334e68 | #194247 | Overrides an inline style |
| CH034 | /html/body/table/tr/td/table/tr[6]/td/p[1] | color | #627d98 | #194247 | Overrides an inline style |
| CH040 | /html/body/table/tr/td/table/tr[6]/td/p[2] | color | #627d98 | #194247 | Overrides an inline style |

### R094 · text.body color: #f6f3f0 (guide line myridius-brand-guide.md:105)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH004 | /html/body/table/tr/td/table/tr[1]/td/p | color | #9fb3c8 | #f6f3f0 | Overrides an inline style |

### R168 · button border-radius: 999px (guide line myridius-brand-guide.md:223)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH028 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | border-radius | (not set) | 999px | Outlook desktop ignores border-radius; other clients show it |

### R172 · button.label font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif (guide line myridius-brand-guide.md:225)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH029 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | font-family | Arial, Helvetica, sans-serif | "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif | Web fonts (Montserrat) load only in clients that support them; others show the fallback fonts; Overrides an inline style |

### R173 · button.label font-weight: 600 (guide line myridius-brand-guide.md:225)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH031 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | font-weight | bold | 600 | Overrides an inline style |

### R174 · button.label letter-spacing: 0.02em (guide line myridius-brand-guide.md:225)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH032 | /html/body/table/tr/td/table/tr[5]/td/table/tr/td/a | letter-spacing | (not set) | 0.02em | Outlook desktop ignores letter-spacing |

### R276 · page.surface background: #f6f3f0 (guide line myridius-brand-guide.md:391)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH002 | /html/body | background-color | #eef1f5 | #f6f3f0 | written as background-color for email clients; Overrides an inline style |

## 3. Understood but not applied

The guide's rule was understood, but could not be applied here.

| Rule | What the guide says | Guide line | Why not |
|---|---|---|---|
| R243 | Use the chart palette in section 2.4. | myridius-brand-guide.md:318 | Chart styling is not supported in V1. |
| R244 | Always start the value legend (1.3, 85, 380) with the first number in the brand-accent color; subsequent numbers in monochrome variants of --quantum-leaf. | myridius-brand-guide.md:319 | Chart styling is not supported in V1. |
| R245 | Bar charts: 4–8px corner radius on bars. Line charts: 2.5px stroke, dotted gridlines rgba(25,66,71,0.08). | myridius-brand-guide.md:320 | Chart styling is not supported in V1. |
| R246 | Tooltip: --carbon-moss background, --base-linen text, 8px radius. | myridius-brand-guide.md:321 | Chart styling is not supported in V1. |
| R224 | Icons: 20px, stroke-style or flat, paired with label. | myridius-brand-guide.md:286 | Icon styling is not supported in V1. |
| R225 | Two icon-container styles: | myridius-brand-guide.md:290 | Icon styling is not supported in V1. |
| R241 | Icons always 1.5–2px stroke, geometric, no emoji, no icons with multi-color fills beyond the brand palette. | myridius-brand-guide.md:310 | Icon styling is not supported in V1. |
| R288 | Use 1.5–2px stroke icons | myridius-brand-guide.md:396 | Icon styling is not supported in V1. |
| R289 | Use filled multicolor emoji icons | myridius-brand-guide.md:396 | Icon styling is not supported in V1. |
| R002 | Brand name \| myridius (lowercase wordmark, camel-case in prose) | myridius-brand-guide.md:10 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R005 | Logo \| Stylized triple-wave "M" mark in mint-green (#52E081) paired with lowercase sans-serif wordmark "myridius" in dark slate (#0C2226 or #194247). Optional… | myridius-brand-guide.md:13 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R006 | Logo placement \| Always bottom-left in headers, footers, panels. Never centered, never inline with body copy. | myridius-brand-guide.md:14 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R119 | Bottom-left corner of page/panel. Footer-left in long pages. | myridius-brand-guide.md:156 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R120 | Center, right-aligned, inline with body copy | myridius-brand-guide.md:156 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R121 | --quantum-leaf wordmark + --pulse-green icon | myridius-brand-guide.md:157 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R122 | Any color other than the two above | myridius-brand-guide.md:157 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R123 | Pure white wordmark — prefer linen for warmth | myridius-brand-guide.md:158 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R124 | --base-linen wordmark + --pulse-green icon | myridius-brand-guide.md:158 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R125 | Transparent background only | myridius-brand-guide.md:159 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R126 | Color background, gradient background, busy imagery directly behind logo | myridius-brand-guide.md:159 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R127 | At least 1× the icon height on all sides | myridius-brand-guide.md:160 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R128 | Cramped next to text or image edges | myridius-brand-guide.md:160 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R129 | Logo height ≥ 24px, ≤ 48px in body; up to 64px in hero | myridius-brand-guide.md:161 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R130 | Tiny (under 20px) or oversized | myridius-brand-guide.md:161 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R131 | Never recolor, outline, rotate, skew, or modify | myridius-brand-guide.md:162 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R132 | Stretch, add effects, swap icon for emoji, replace with text | myridius-brand-guide.md:162 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R133 | If logo asset is unavailable, render a placeholder mark: a circular green badge with M in italic Montserrat weight 600, paired with myridius™ wordmark. | myridius-brand-guide.md:164 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R215 | Logomark left (logo, not full wordmark). | myridius-brand-guide.md:275 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R280 | Place logo bottom-left | myridius-brand-guide.md:393 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R281 | Center logo or put it next to nav links | myridius-brand-guide.md:393 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R329 | Myridius = light-primary, Montserrat-only, signal-teal (#09A78D) accent, mint-green logo, asymmetric white space, organic wave ornament, confident-and-calm voi… | myridius-brand-guide.md:512 | Logo is applied only when a logo asset is supplied; this tool never invents a logo. |
| R135 | Fluid, asymmetric, vector shape hugging the right edge of section dividers and section transitions. Composition rules: | myridius-brand-guide.md:174 | Needs a design asset (wave artwork); none supplied. |
| R136 | 100–300 flowing parallel curves, hairline weight (0.75–1.5px), color --virtual-tide at 30–60% opacity. | myridius-brand-guide.md:176 | Needs a design asset (wave artwork); none supplied. |
| R137 | Curves originate from bottom-right corner, fan upward and outward, leaving white/linen space on the inside. | myridius-brand-guide.md:177 | Needs a design asset (wave artwork); none supplied. |
| R138 | On dark surfaces, use --pulse-green or --neural-beam at low opacity. | myridius-brand-guide.md:178 | Needs a design asset (wave artwork); none supplied. |
| R139 | Always decorative — never carry informational content. | myridius-brand-guide.md:179 | Needs a design asset (wave artwork); none supplied. |
| R140 | Sizing: takes up 30–50% of viewport width at section dividers; smaller (10–20%) as decorative bands in lighter sections. | myridius-brand-guide.md:180 | Needs a design asset (wave artwork); none supplied. |
| R282 | Use the wave ornament on dividers | myridius-brand-guide.md:394 | Needs a design asset (wave artwork); none supplied. |
| R148 | card.gradient border: 1px solid rgba(82, 224, 129, 0.15) | myridius-brand-guide.md:203 | No applier supports 'css_declaration' rules yet (deferred) |
| R149 | card.gradient border-radius: 12px | myridius-brand-guide.md:204 | No applier supports 'css_declaration' rules yet (deferred) |
| R180 | interactive.focus outline: 2px solid #09a78d | myridius-brand-guide.md:228 | No applier supports 'focus' rules yet (deferred) |
| R284 | Never use the 'glow' effect | myridius-brand-guide.md:394 | No applier supports 'forbid_effect' rules yet (deferred) |
| R285 | Never use the 'glassmorphism' effect | myridius-brand-guide.md:394 | No applier supports 'forbid_effect' rules yet (deferred) |
| R175 | button.destructive background: #c84b47 | myridius-brand-guide.md:226 | No element in the artifact has the role 'button.destructive' |
| R176 | button.destructive color: #ffffff | myridius-brand-guide.md:226 | No element in the artifact has the role 'button.destructive' |
| R177 | button.disabled opacity: 0.5 | myridius-brand-guide.md:227 | No element in the artifact has the role 'button.disabled' |
| R178 | button.disabled cursor: not-allowed | myridius-brand-guide.md:227 | No element in the artifact has the role 'button.disabled' |
| R179 | button.disabled pointer-events: none | myridius-brand-guide.md:227 | No element in the artifact has the role 'button.disabled' |
| R164 | button.icon background: transparent | myridius-brand-guide.md:221 | No element in the artifact has the role 'button.icon' |
| R166 | button.icon border: none | myridius-brand-guide.md:221 | No element in the artifact has the role 'button.icon' |
| R170 | button.large padding: 16px 36px | myridius-brand-guide.md:224 | No element in the artifact has the role 'button.large' |
| R169 | button.medium padding: 12px 28px | myridius-brand-guide.md:224 | No element in the artifact has the role 'button.medium' |
| R151 | button.primary background: #09a78d | myridius-brand-guide.md:218 | No element in the artifact has the role 'button.primary' |
| R152 | button.primary color: #ffffff | myridius-brand-guide.md:218 | No element in the artifact has the role 'button.primary' |
| R153 | button.primary border: none | myridius-brand-guide.md:218 | No element in the artifact has the role 'button.primary' |
| R155 | button.secondary background: transparent | myridius-brand-guide.md:219 | No element in the artifact has the role 'button.secondary' |
| R156 | button.secondary color: #194247 | myridius-brand-guide.md:219 | No element in the artifact has the role 'button.secondary' |
| R157 | button.secondary color: #f6f3f0 | myridius-brand-guide.md:219 | No element in the artifact has the role 'button.secondary' |
| R158 | button.secondary border: 1.5px solid currentcolor | myridius-brand-guide.md:219 | No element in the artifact has the role 'button.secondary' |
| R171 | button.small padding: 8px 16px | myridius-brand-guide.md:224 | No element in the artifact has the role 'button.small' |
| R160 | button.tertiary background: transparent | myridius-brand-guide.md:220 | No element in the artifact has the role 'button.tertiary' |
| R161 | button.tertiary color: #09a78d | myridius-brand-guide.md:220 | No element in the artifact has the role 'button.tertiary' |
| R162 | button.tertiary border: none | myridius-brand-guide.md:220 | No element in the artifact has the role 'button.tertiary' |
| R206 | form.helper font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif | myridius-brand-guide.md:262 | No element in the artifact has the role 'form.helper' |
| R207 | form.helper font-weight: 400 | myridius-brand-guide.md:262 | No element in the artifact has the role 'form.helper' |
| R208 | form.helper font-size: 13px | myridius-brand-guide.md:262 | No element in the artifact has the role 'form.helper' |
| R209 | form.helper color: #337077 | myridius-brand-guide.md:262 | No element in the artifact has the role 'form.helper' |
| R201 | form.label font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif | myridius-brand-guide.md:261 | No element in the artifact has the role 'form.label' |
| R202 | form.label font-weight: 600 | myridius-brand-guide.md:261 | No element in the artifact has the role 'form.label' |
| R203 | form.label font-size: 14px | myridius-brand-guide.md:261 | No element in the artifact has the role 'form.label' |
| R204 | form.label color: #194247 | myridius-brand-guide.md:261 | No element in the artifact has the role 'form.label' |
| R037 | heading.display font-size: clamp(3rem, 6vw + 1rem, 6rem) | myridius-brand-guide.md:88 | No element in the artifact has the role 'heading.display' |
| R038 | heading.display font-weight: 800 | myridius-brand-guide.md:88 | No element in the artifact has the role 'heading.display' |
| R039 | heading.display line-height: 1.05 | myridius-brand-guide.md:88 | No element in the artifact has the role 'heading.display' |
| R040 | heading.display letter-spacing: -0.02em | myridius-brand-guide.md:88 | No element in the artifact has the role 'heading.display' |
| R049 | heading.h3 font-size: clamp(1.375rem, 1.5vw + 0.5rem, 1.875rem) | myridius-brand-guide.md:91 | No element in the artifact has the role 'heading.h3' |
| R050 | heading.h3 font-weight: 600 | myridius-brand-guide.md:91 | No element in the artifact has the role 'heading.h3' |
| R051 | heading.h3 line-height: 1.25 | myridius-brand-guide.md:91 | No element in the artifact has the role 'heading.h3' |
| R052 | heading.h3 letter-spacing: -0.005em | myridius-brand-guide.md:91 | No element in the artifact has the role 'heading.h3' |
| R053 | heading.h4 font-size: 1.25rem | myridius-brand-guide.md:92 | No element in the artifact has the role 'heading.h4' |
| R054 | heading.h4 font-weight: 600 | myridius-brand-guide.md:92 | No element in the artifact has the role 'heading.h4' |
| R055 | heading.h4 line-height: 1.3 | myridius-brand-guide.md:92 | No element in the artifact has the role 'heading.h4' |
| R056 | heading.h4 letter-spacing: 0 | myridius-brand-guide.md:92 | No element in the artifact has the role 'heading.h4' |
| R195 | input background: #ffffff | myridius-brand-guide.md:257 | No element in the artifact has the role 'input' |
| R196 | input border: 1px solid #19424729 | myridius-brand-guide.md:257 | No element in the artifact has the role 'input' |
| R198 | input padding: 14px 16px | myridius-brand-guide.md:259 | No element in the artifact has the role 'input' |
| R199 | input.focus border: 2px solid #09a78d | myridius-brand-guide.md:260 | No element in the artifact has the role 'input.focus' |
| R200 | input.focus box-shadow: 0 0 0 4px #09a78d26 | myridius-brand-guide.md:260 | No element in the artifact has the role 'input.focus' |
| R069 | text.caption font-size: 0.8125rem | myridius-brand-guide.md:96 | No element in the artifact has the role 'text.caption' |
| R070 | text.caption font-weight: 500 | myridius-brand-guide.md:96 | No element in the artifact has the role 'text.caption' |
| R071 | text.caption line-height: 1.45 | myridius-brand-guide.md:96 | No element in the artifact has the role 'text.caption' |
| R072 | text.caption letter-spacing: 0.04em | myridius-brand-guide.md:96 | No element in the artifact has the role 'text.caption' |
| R073 | text.eyebrow font-size: 0.75rem | myridius-brand-guide.md:97 | No element in the artifact has the role 'text.eyebrow' |
| R074 | text.eyebrow font-weight: 600 | myridius-brand-guide.md:97 | No element in the artifact has the role 'text.eyebrow' |
| R075 | text.eyebrow line-height: 1.4 | myridius-brand-guide.md:97 | No element in the artifact has the role 'text.eyebrow' |
| R076 | text.eyebrow letter-spacing: 0.12em | myridius-brand-guide.md:97 | No element in the artifact has the role 'text.eyebrow' |
| R089 | text.eyebrow text-transform: uppercase | myridius-brand-guide.md:104 | No element in the artifact has the role 'text.eyebrow' |
| R091 | text.eyebrow color: #09a78d | myridius-brand-guide.md:104 | No element in the artifact has the role 'text.eyebrow' |
| R092 | text.eyebrow color: #52e081 | myridius-brand-guide.md:104 | No element in the artifact has the role 'text.eyebrow' |
| R057 | text.lead font-size: 1.125rem | myridius-brand-guide.md:93 | No element in the artifact has the role 'text.lead' |
| R058 | text.lead font-weight: 400 | myridius-brand-guide.md:93 | No element in the artifact has the role 'text.lead' |
| R059 | text.lead line-height: 1.6 | myridius-brand-guide.md:93 | No element in the artifact has the role 'text.lead' |
| R060 | text.lead letter-spacing: 0 | myridius-brand-guide.md:93 | No element in the artifact has the role 'text.lead' |
| R081 | text.quote font-size: inherit | myridius-brand-guide.md:99 | No element in the artifact has the role 'text.quote' |
| R082 | text.quote font-weight: 400 | myridius-brand-guide.md:99 | No element in the artifact has the role 'text.quote' |
| R083 | text.quote font-style: italic | myridius-brand-guide.md:99 | No element in the artifact has the role 'text.quote' |
| R084 | text.quote line-height: inherit | myridius-brand-guide.md:99 | No element in the artifact has the role 'text.quote' |
| R085 | text.quote letter-spacing: inherit | myridius-brand-guide.md:99 | No element in the artifact has the role 'text.quote' |
| R065 | text.secondary font-size: 0.9375rem | myridius-brand-guide.md:95 | No element in the artifact has the role 'text.secondary' |
| R066 | text.secondary font-weight: 400 | myridius-brand-guide.md:95 | No element in the artifact has the role 'text.secondary' |
| R067 | text.secondary line-height: 1.55 | myridius-brand-guide.md:95 | No element in the artifact has the role 'text.secondary' |
| R068 | text.secondary letter-spacing: 0 | myridius-brand-guide.md:95 | No element in the artifact has the role 'text.secondary' |
| R078 | button.label font-weight: 600 | myridius-brand-guide.md:98 | Overridden by rule R173 (more specific, or later in the guide) for font-weight |
| R080 | button.label letter-spacing: 0.02em | myridius-brand-guide.md:98 | Overridden by rule R174 (more specific, or later in the guide) for letter-spacing |
| R247 | Always use authentic, warm-toned, real-people photography. | myridius-brand-guide.md:325 | Photo grading needs image processing; V1 does not alter images. |
| R248 | NEVER stock-clipart, posed studio shots, AI-generated faces. | myridius-brand-guide.md:326 | Photo grading needs image processing; V1 does not alter images. |
| R249 | Default photo treatment: subtle desaturation (-10%), color graded toward the brand teal range. | myridius-brand-guide.md:327 | Photo grading needs image processing; V1 does not alter images. |
| R250 | Photo overlays: 40–60% --carbon-moss gradient from bottom to allow white text on top. | myridius-brand-guide.md:328 | Photo grading needs image processing; V1 does not alter images. |
| R251 | Aspect ratios: 4:5 (portrait, photo-left), 16:9 (hero), 3:2 (cards). | myridius-brand-guide.md:329 | Photo grading needs image processing; V1 does not alter images. |
| R296 | Paste the block below verbatim into v0 / Cursor / Bolt / Lovable / Claude Code when generating the site: | myridius-brand-guide.md:405 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R297 | Build a website/portal in the Myridius brand system. Follow this spec exactly. | myridius-brand-guide.md:408 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R298 | ## Brand - Brand name: myridius - Voice: confident, calm, expert, human. Plain language, no hype. | myridius-brand-guide.md:410 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R299 | Logo: stylized wave "M" in mint-green (#52E081) + lowercase Montserrat wordmark. Always bottom-left. | myridius-brand-guide.md:413 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R300 | ## Typography - Single typeface: Montserrat — bold for headlines, regular for body. - Display: clamp(3rem, 6vw+1rem, 6rem), weight 800, line-height 1.05, lette… | myridius-brand-guide.md:415 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R301 | ## Color palette (CSS variables) Light surface (default page): --cloud-white: #FFFFFF --base-linen: #F6F3F0 ← PRIMARY background --quantum-leaf: #194247 ← prim… | myridius-brand-guide.md:424 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R302 | ## Background policy - Primary surfaces = LIGHT (--base-linen or --cloud-white). Most pages should feel airy. - Dark surfaces (--carbon-moss) appear in: hero s… | myridius-brand-guide.md:437 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R303 | Alternate light/dark sections rhythmically. Never two dark sections back-to-back. | myridius-brand-guide.md:440 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R304 | ## Layout principles - 8pt spacing scale. Page max-width 1280px. 12-column grid, 32px gap. - Section vertical padding 96–128px on desktop. - Generous whitespac… | myridius-brand-guide.md:442 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R305 | ## Signature elements (mandatory) 1. Organic wave ornament — flowing parallel curves on right edge of dividers/heroes. Color #09A78D at 30–60% opacity, hairlin… | myridius-brand-guide.md:449 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R306 | Logo placement — always bottom-left. | myridius-brand-guide.md:451 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R307 | Hand-drawn annotations (in template/docs/empty states only, never in shipped marketing UI) — Caveat handwriting font, color #E5FD84, with curved arrow, leading… | myridius-brand-guide.md:452 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R308 | 4. Gradient fade-cards on dark sections — cards that fade to transparent on the right, appearing to float out of the background. | myridius-brand-guide.md:453 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R309 | ## Components Buttons (pill --radius-pill 999px or rectangular 8px): Primary: bg #09A78D, text #FFFFFF. Hover: darken 8%, lift, soft shadow. Secondary: transpa… | myridius-brand-guide.md:455 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R311 | Cards: On light: white bg, 1px subtle border (#194247 at 8% opacity), radius 12px, shadow 0 1px 3px rgba(12,34,38,0.04). On dark: gradient fade-card (light tin… | myridius-brand-guide.md:462 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R312 | Forms: Inputs white, border 1px solid rgba(25,66,71,0.16), radius 12px. Focus border becomes 2px solid #09A78D with 4px outer glow. | myridius-brand-guide.md:466 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R313 | Icons: | myridius-brand-guide.md:470 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R314 | Geometric, 1.5–2px stroke. Single brand color (--pulse-green or --quantum-leaf). NEVER emoji. | myridius-brand-guide.md:471 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R315 | Navigation: Light surface top nav (72px, semi-transparent linen with backdrop-blur). Dashboard side nav (260px, --carbon-moss surface) for portal pages. | myridius-brand-guide.md:473 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R316 | Charts: Use the chart palette in order. 4–8px corner radius on bars. Dotted gridlines. Tooltip on --carbon-moss. | myridius-brand-guide.md:477 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R317 | ## Imagery - Authentic, real-people photography. Warm color grade. | myridius-brand-guide.md:480 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R318 | Always desaturate -10% to push toward brand teal range. | myridius-brand-guide.md:482 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R319 | - Aspect ratios: 4:5 (portrait), 16:9 (hero), 3:2 (cards). - Dark gradient overlays (45% --carbon-moss) on photos for white text legibility. | myridius-brand-guide.md:483 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R320 | ## Page structure (default) 1. Top nav (light, blur) 2. Hero — light or dark, with wave ornament 3. Light content section (3-col feature grid or stat row) 4. L… | myridius-brand-guide.md:486 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R321 | ## Hard rules (NEVER violate) | myridius-brand-guide.md:495 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R322 | Only Montserrat. Never Poppins, Inter, serif, or display fonts. | myridius-brand-guide.md:496 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R323 | Always logo bottom-left. | myridius-brand-guide.md:498 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R324 | Always include focus states on interactive elements. | myridius-brand-guide.md:499 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R325 | - Body text contrast ratio ≥ 4.5:1. - No emoji as UI icons. No AI-generated faces. No clipart. | myridius-brand-guide.md:500 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R326 | Wave ornament is decorative — never carries information. | myridius-brand-guide.md:502 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R327 | - Keep annotations out of shipped marketing UI. | myridius-brand-guide.md:503 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R328 | Build the [page/portal/landing] now. Output a self-contained HTML/CSS/JS file with the design system in :root CSS variables and semantic HTML. | myridius-brand-guide.md:505 | Prompt for generating new sites; only the directives it states are read, the rest is not applied. |
| R252 | [Top Nav 72px — light, blur, semi-transparent] [Hero Section — 100vh on landing, 60vh on inner — light OR dark] [Content Section 1 — light, generous padding] [… | myridius-brand-guide.md:338 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R253 | Rule: alternate light/dark sections for visual rhythm. Never two dark sections in a row. Never two sections of identical composition. | myridius-brand-guide.md:347 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R254 | Light hero, text-left, wave-right — most common. Headline + sub + 2 CTAs in left 50%. Wave ornament + product screenshot or stock image in right 50%. | myridius-brand-guide.md:351 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R255 | Dark hero, photo-top — full-width lifestyle photo top 40%, dark section below with headline + CTAs. | myridius-brand-guide.md:352 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R256 | Dark hero, photo-left — vertical full-bleed photo left 30%, dark surface right 70% with text. | myridius-brand-guide.md:353 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R257 | Dark hero with radial bar chart — dark surface, headline top-left, decorative ring chart bottom-right. | myridius-brand-guide.md:354 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R258 | Section-divider-style — full-bleed dark teal background with single bold sentence left-aligned, wave ornament right. | myridius-brand-guide.md:355 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R259 | Three-column feature grid (most-used). Column heading + icon-container + 2-3 line body. All columns equal width 1fr; gap 32px. | myridius-brand-guide.md:359 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R260 | Four-column process steps. Each card numbered 01–04 in colored top-strip; bold title; supporting copy. | myridius-brand-guide.md:360 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R261 | Stat row — three to four large numbers with unit and one-line context. Used at top of overview pages. | myridius-brand-guide.md:361 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R262 | Two-column comparison — 60% content left, 40% visual right; or 40/60 reversed. | myridius-brand-guide.md:362 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R263 | Carousel / logo wall — single row of partner/customer logos, grayscale by default, full-color on hover. | myridius-brand-guide.md:363 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R264 | 96px between major page sections on desktop, 64px on mobile. | myridius-brand-guide.md:367 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R265 | 48px between sub-blocks within a section. | myridius-brand-guide.md:368 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R266 | 24px between heading group and body. | myridius-brand-guide.md:369 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R267 | 16px between heading and eyebrow. | myridius-brand-guide.md:370 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R268 | Body paragraphs max-width: 65ch. | myridius-brand-guide.md:371 | Restructuring page layout is out of scope for V1; artifact structure is preserved. |
| R041 | heading.h1 font-size: clamp(2.25rem, 4vw + 1rem, 4rem) | myridius-brand-guide.md:89 | clamp() is not supported by most email clients |
| R045 | heading.h2 font-size: clamp(1.75rem, 2.5vw + 0.75rem, 2.75rem) | myridius-brand-guide.md:90 | clamp() is not supported by most email clients |

## 4. Could not interpret

Guidance the tool could not turn into a checkable rule. Nothing here was guessed or applied.

| Reason | Count |
|---|---|
| No extractor understood this text. | 35 |
| CSS has no selector, so the element it targets is unknown | 26 |
| Directive wording is not one of the supported patterns. | 14 |
| Subjective guidance about tone cannot be checked mechanically; content is never rewritten. | 6 |
| Hover behaviour is described in prose, not as property values. | 4 |
| 3.3 Style Rules 'Headlines': not a single value | 3 |
| No element role known for selector 'span' | 3 |
| 3.3 Style Rules 'Eyebrow labels': not a single value | 1 |
| Cannot resolve color value 'current' | 1 |
| 7.3 Forms 'Border radius': gives alternatives with no rule for choosing between them | 1 |
| 7.3 Forms 'Label': instruction not supported | 1 |

| Rule | Guide line | Text | Reason |
|---|---|---|---|
| R090 | myridius-brand-guide.md:104 | letter-spacing +0.08em to +0.12em | 3.3 Style Rules 'Eyebrow labels': not a single value |
| R086 | myridius-brand-guide.md:103 | Bold (700+) | 3.3 Style Rules 'Headlines': not a single value |
| R087 | myridius-brand-guide.md:103 | tight line-height (1.05–1.15) | 3.3 Style Rules 'Headlines': not a single value |
| R088 | myridius-brand-guide.md:103 | slightly negative letter-spacing | 3.3 Style Rules 'Headlines': not a single value |
| R197 | myridius-brand-guide.md:258 | 12px (modern) or 8px (compact) | 7.3 Forms 'Border radius': gives alternatives with no rule for choosing between them |
| R205 | myridius-brand-guide.md:261 | sits above input | 7.3 Forms 'Label': instruction not supported |
| R184 | myridius-brand-guide.md:237 | #FFFFFF | CSS has no selector, so the element it targets is unknown |
| R185 | myridius-brand-guide.md:238 | 1px solid rgba(25, 66, 71, 0.08) | CSS has no selector, so the element it targets is unknown |
| R186 | myridius-brand-guide.md:239 | 12px | CSS has no selector, so the element it targets is unknown |
| R187 | myridius-brand-guide.md:240 | 32px | CSS has no selector, so the element it targets is unknown |
| R188 | myridius-brand-guide.md:241 | 0 1px 3px rgba(12, 34, 38, 0.04) | CSS has no selector, so the element it targets is unknown |
| R190 | myridius-brand-guide.md:247 | linear-gradient(135deg, rgba(82,224,129,0.06) 0%, rgba(9,167,141,0.02) 50%, transparent 100%) | CSS has no selector, so the element it targets is unknown |
| R191 | myridius-brand-guide.md:248 | 1px solid rgba(82, 224, 129, 0.12) | CSS has no selector, so the element it targets is unknown |
| R192 | myridius-brand-guide.md:249 | 20px | CSS has no selector, so the element it targets is unknown |
| R193 | myridius-brand-guide.md:250 | 40px | CSS has no selector, so the element it targets is unknown |
| R211 | myridius-brand-guide.md:269 | rgba(246, 243, 240, 0.85) | CSS has no selector, so the element it targets is unknown |
| R212 | myridius-brand-guide.md:270 | saturate(140%) blur(12px) | CSS has no selector, so the element it targets is unknown |
| R213 | myridius-brand-guide.md:271 | 1px solid rgba(25,66,71,0.08) | CSS has no selector, so the element it targets is unknown |
| R214 | myridius-brand-guide.md:272 | 72px | CSS has no selector, so the element it targets is unknown |
| R227 | myridius-brand-guide.md:295 | 64px | CSS has no selector, so the element it targets is unknown |
| R228 | myridius-brand-guide.md:295 | 64px | CSS has no selector, so the element it targets is unknown |
| R229 | myridius-brand-guide.md:295 | 50% | CSS has no selector, so the element it targets is unknown |
| R230 | myridius-brand-guide.md:296 | #52E081 | CSS has no selector, so the element it targets is unknown |
| R231 | myridius-brand-guide.md:297 | #0C2226 | CSS has no selector, so the element it targets is unknown |
| R232 | myridius-brand-guide.md:298 | grid | CSS has no selector, so the element it targets is unknown |
| R233 | myridius-brand-guide.md:298 | center | CSS has no selector, so the element it targets is unknown |
| R235 | myridius-brand-guide.md:304 | 56px | CSS has no selector, so the element it targets is unknown |
| R236 | myridius-brand-guide.md:304 | 56px | CSS has no selector, so the element it targets is unknown |
| R237 | myridius-brand-guide.md:304 | 50% | CSS has no selector, so the element it targets is unknown |
| R238 | myridius-brand-guide.md:305 | #0C2226 | CSS has no selector, so the element it targets is unknown |
| R239 | myridius-brand-guide.md:306 | #52E081 | CSS has no selector, so the element it targets is unknown |
| R240 | myridius-brand-guide.md:307 | 1px solid #52E081 | CSS has no selector, so the element it targets is unknown |
| R165 | myridius-brand-guide.md:221 | current | Cannot resolve color value 'current' |
| R033 | myridius-brand-guide.md:69 | Always run a contrast check before selecting text color. | Directive wording is not one of the supported patterns. |
| R242 | myridius-brand-guide.md:314 | Display numbers in Montserrat 800 weight, --fs-display for hero metrics, --fs-h1 on detail pages. Color: --virtual-tide on light, --pulse-green on dark. Always… | Directive wording is not one of the supported patterns. |
| R275 | myridius-brand-guide.md:390 | Mix in Poppins, Inter, serif, or display fonts | Directive wording is not one of the supported patterns. |
| R277 | myridius-brand-guide.md:391 | Make the entire site dark | Directive wording is not one of the supported patterns. |
| R278 | myridius-brand-guide.md:392 | Alternate light / dark sections | Directive wording is not one of the supported patterns. |
| R279 | myridius-brand-guide.md:392 | Stack 3+ dark sections in a row | Directive wording is not one of the supported patterns. |
| R286 | myridius-brand-guide.md:395 | Use --virtual-tide for accent only | Directive wording is not one of the supported patterns. |
| R287 | myridius-brand-guide.md:395 | Color body text in pulses/lime yellow on light | Directive wording is not one of the supported patterns. |
| R290 | myridius-brand-guide.md:397 | Hand-drawn annotations in template docs only | Directive wording is not one of the supported patterns. |
| R291 | myridius-brand-guide.md:397 | Leave them in shipped product UI | Directive wording is not one of the supported patterns. |
| R292 | myridius-brand-guide.md:398 | Use authentic photography | Directive wording is not one of the supported patterns. |
| R293 | myridius-brand-guide.md:398 | Use AI-generated faces or stock clipart | Directive wording is not one of the supported patterns. |
| R294 | myridius-brand-guide.md:399 | Maintain 4.5:1 text contrast | Directive wording is not one of the supported patterns. |
| R295 | myridius-brand-guide.md:399 | Sacrifice accessibility for color expressiveness | Directive wording is not one of the supported patterns. |
| R154 | myridius-brand-guide.md:218 | darken 8%, lift translateY(-1px), shadow 0 8px 24px rgba(9,167,141,0.25) | Hover behaviour is described in prose, not as property values. |
| R159 | myridius-brand-guide.md:219 | fill with tint at 10% opacity | Hover behaviour is described in prose, not as property values. |
| R163 | myridius-brand-guide.md:220 | underline grows | Hover behaviour is described in prose, not as property values. |
| R167 | myridius-brand-guide.md:221 | background tint | Hover behaviour is described in prose, not as property values. |
| R142 | myridius-brand-guide.md:188 | "Caveat", cursive | No element role known for selector 'span' |
| R143 | myridius-brand-guide.md:188 | #E5FD84 | No element role known for selector 'span' |
| R144 | myridius-brand-guide.md:188 | 14px | No element role known for selector 'span' |
| R001 | myridius-brand-guide.md:2 | A reference for AI software development tools (v0, Cursor, Bolt, Lovable, Claude Code, etc.) to build a website/portal in this brand. | No extractor understood this text. |
| R003 | myridius-brand-guide.md:11 | Voice \| Confident, calm, expert, human. Plain language with technical authority. Never hype-y, never salesy. | No extractor understood this text. |
| R004 | myridius-brand-guide.md:12 | Personality \| Modern, sophisticated, quietly innovative, trustworthy, accessible to non-experts. | No extractor understood this text. |
| R007 | myridius-brand-guide.md:20 | Use CSS variables. Primary canvas is light (Base Linen). Dark surfaces appear in section dividers, hero areas, callouts, modals. | No extractor understood this text. |
| R016 | myridius-brand-guide.md:37 | When surface is --carbon-moss (#0C2226): | No extractor understood this text. |
| R023 | myridius-brand-guide.md:50 | When surface is --base-linen (#F6F3F0) or --cloud-white: | No extractor understood this text. |
| R028 | myridius-brand-guide.md:61 | For graphs, tables, dashboards (ordered): | No extractor understood this text. |
| R029 | myridius-brand-guide.md:63 | #52E081 → #337077 → #09A78D → #94DEA5 → #CBEBBD → #DBF4D0 → #285C62 → #163439 → #E5FD84 → #10B18E | No extractor understood this text. |
| R034 | myridius-brand-guide.md:75 | Single typeface family for the entire product. This replaces whatever the original deck used. | No extractor understood this text. |
| R095 | myridius-brand-guide.md:106 | Italic in display rules: Use italic Montserrat (400 italic) for editorial pull-quotes and signature accents — e.g. *"The Competitive Edge"*. | No extractor understood this text. |
| R109 | myridius-brand-guide.md:133 | Page max-width: 1280px, with max-width: 1440px for marketing hero sections. | No extractor understood this text. |
| R110 | myridius-brand-guide.md:134 | Container padding: clamp(20px, 4vw, 56px) left/right. | No extractor understood this text. |
| R111 | myridius-brand-guide.md:135 | Column system: 12-column grid, gap: 32px on desktop, 16px on mobile. | No extractor understood this text. |
| R112 | myridius-brand-guide.md:136 | Common splits: 50/50, 40/60 (text-block-heavy slides), 30/70 (photo-left hero). | No extractor understood this text. |
| R113 | myridius-brand-guide.md:137 | Vertical rhythm: 48–96px between major sections; 24–32px between sub-elements. | No extractor understood this text. |
| R118 | myridius-brand-guide.md:148 | Card radius: 12–20px. Button radius: 999px (pill) by default — or 8px for square buttons. Input fields: 8–12px. | No extractor understood this text. |
| R134 | myridius-brand-guide.md:170 | These three elements appear in nearly every slide. Web versions of them are mandatory for visual coherence: | No extractor understood this text. |
| R141 | myridius-brand-guide.md:184 | Tiny informal notes in bright lime/yellow (--neural-beam), with a small curved arrow. These are an internal-template marker — use them on docs, onboarding over… | No extractor understood this text. |
| R146 | myridius-brand-guide.md:198 | Cards on dark surfaces that fade to transparent on the right edge — they appear to float out of the background. Implement as: | No extractor understood this text. |
| R150 | myridius-brand-guide.md:208 | Use for: info callouts, stat blocks, content cards on dark hero sections. | No extractor understood this text. |
| R182 | myridius-brand-guide.md:232 | Two main patterns: | No extractor understood this text. |
| R183 | myridius-brand-guide.md:234 | (a) Light surface card (on --base-linen page): | No extractor understood this text. |
| R189 | myridius-brand-guide.md:244 | (b) Dark surface gradient card (on --carbon-moss section): | No extractor understood this text. |
| R194 | myridius-brand-guide.md:253 | Cards may carry a color-coded header strip (8px tall top bar in sequence: --pulse-green → --virtual-tide → --digital-pavo → --neural-beam) when they represent … | No extractor understood this text. |
| R210 | myridius-brand-guide.md:266 | Top nav on light backgrounds: | No extractor understood this text. |
| R216 | myridius-brand-guide.md:276 | Links centered or right-aligned, Montserrat 500 15px. | No extractor understood this text. |
| R217 | myridius-brand-guide.md:277 | Active link: 2px underline --virtual-tide, 4px below text. | No extractor understood this text. |
| R218 | myridius-brand-guide.md:278 | CTA on the far right: --virtual-tide pill button. | No extractor understood this text. |
| R219 | myridius-brand-guide.md:280 | Side nav for portal/dashboard pages: | No extractor understood this text. |
| R220 | myridius-brand-guide.md:282 | Width: 260px (collapsed: 72px). | No extractor understood this text. |
| R221 | myridius-brand-guide.md:283 | Background: --carbon-moss. | No extractor understood this text. |
| R222 | myridius-brand-guide.md:284 | Link color: --base-linen. | No extractor understood this text. |
| R223 | myridius-brand-guide.md:285 | Active link: 4px left bar in --pulse-green, surface gets rgba(82,224,129,0.06) tint. | No extractor understood this text. |
| R226 | myridius-brand-guide.md:292 | (a) Filled circle (services / features): | No extractor understood this text. |
| R234 | myridius-brand-guide.md:301 | (b) Outline circle (cards on light): | No extractor understood this text. |
| R269 | myridius-brand-guide.md:377 | Active voice. "We help you ship faster" not "Faster shipping is enabled by our platform." | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |
| R270 | myridius-brand-guide.md:378 | Plain over clever. Skip "synergize", "leverage", "delve". | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |
| R271 | myridius-brand-guide.md:379 | Confident without hype. "Trusted by 380M+ users" is fine. "The world's #1 most amazing platform" is not. | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |
| R272 | myridius-brand-guide.md:380 | Format eyebrows as ALL CAPS short labels (3–5 words max), followed by sentence-case headline. | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |
| R273 | myridius-brand-guide.md:381 | Sentence case in headlines (only first word capitalized, except proper nouns). | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |
| R274 | myridius-brand-guide.md:382 | CTA copy is action-oriented: "View case study" / "Book a demo" / "Get started" / "Explore platform". Avoid "Submit" and "Click here". | Subjective guidance about tone cannot be checked mechanically; content is never rewritten. |

## 5. Contradictions in the guide

### C001 · UNRESOLVED: neither side applied

Guide forbids 'gradient' but also specifies 2 style(s) that use it

| Rule | What it says | Guide line | Final status |
|---|---|---|---|
| R147 | card.gradient background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 60%, transparent 100%) | myridius-brand-guide.md:202 | Conflict (unresolved) |
| R190 | background: linear-gradient(135deg, rgba(82,224,129,0.06) 0%, rgba(9,167,141,0.02) 50%, transparent 100%) | myridius-brand-guide.md:247 | Could not interpret |
| R283 | Never use the 'gradient' effect | myridius-brand-guide.md:394 | Conflict (unresolved) |

### C002 · resolved by the guide itself

Guide allows only ['montserrat'] but also uses 'Caveat' in 1 style(s)

Resolution: Resolved by the guide's own exception at myridius-brand-guide.md:194. The guide limits it to: developer docs, internal templates, and template-builder UIs

| Rule | What it says | Guide line | Final status |
|---|---|---|---|
| R096 | Only the font Montserrat may be used | myridius-brand-guide.md:107 | Applied |
| R142 | font-family: "Caveat", cursive | myridius-brand-guide.md:188 | Could not interpret |
| R145 | The font Caveat is allowed, but only in: The guide limits it to: developer docs, internal templates, and template-builder UIs | myridius-brand-guide.md:194 | Reference definition |

### C003 · UNRESOLVED: neither side applied

interactive.focus outline-offset is set to different values: ['2px', '4px']

| Rule | What it says | Guide line | Final status |
|---|---|---|---|
| R181 | interactive.focus outline-offset: 2px | myridius-brand-guide.md:228 | Conflict (unresolved) |
| R310 | interactive.focus outline-offset: 4px | myridius-brand-guide.md:460 | Conflict (unresolved) |

## 6. Reference definitions

Understood and used as input by other rules; nothing to apply on their own: 18 × color_token, 16 × css_variable, 1 × font_exception. Full list in `guide_rules.json`.

## 7. Changes rolled back

Edits that were planned, then undone because they would have broken the result. The page keeps its own value there.

_None._

## 8. Other places a rule was skipped

| Times | Reason |
|---|---|
| 7 | No element in the artifact has the role 'text.eyebrow' |
| 5 | No element in the artifact has the role 'text.quote' |
| 4 | No element in the artifact has the role 'heading.display' |
| 4 | No element in the artifact has the role 'heading.h3' |
| 4 | No element in the artifact has the role 'heading.h4' |
| 4 | No element in the artifact has the role 'text.lead' |
| 4 | No element in the artifact has the role 'text.secondary' |
| 4 | No element in the artifact has the role 'text.caption' |
| 4 | No element in the artifact has the role 'button.secondary' |
| 4 | No element in the artifact has the role 'form.label' |
| 4 | No element in the artifact has the role 'form.helper' |
| 3 | No element in the artifact has the role 'button.primary' |
| 3 | No element in the artifact has the role 'button.tertiary' |
| 3 | No element in the artifact has the role 'button.disabled' |
| 3 | No element in the artifact has the role 'input' |
| 2 | clamp() is not supported by most email clients |
| 2 | No element in the artifact has the role 'button.icon' |
| 2 | No element in the artifact has the role 'button.destructive' |
| 2 | No element in the artifact has the role 'input.focus' |
| 1 | No element in the artifact has the role 'button.medium' |
| 1 | No element in the artifact has the role 'button.large' |
| 1 | No element in the artifact has the role 'button.small' |
| 1 | Overridden by rule R172 (more specific, or later in the guide) for font-family |
| 1 | Overridden by rule R173 (more specific, or later in the guide) for font-weight |
| 1 | Overridden by rule R174 (more specific, or later in the guide) for letter-spacing |

## 9. Elements with text but no role

1 element(s) have text but match no role, so brand rules did not target them (only the font family was enforced).

- `/html/body/div <div> line 27`

## Notes and limits

- 1 conditional style block(s) (@media, @supports) were not evaluated
- 5 Outlook conditional comment(s) were left untouched; Outlook desktop may still show the original styling inside them
- Wrote inline styles on 9 element(s); no <style> block or marker attributes were added
- Montserrat loads only in email clients that support web fonts (for example Apple Mail); other clients show the fallback fonts

