# Acme Conflicting Guide

*A guide that contradicts itself twice. Synthetic.*

## 1. Brand Identity

Acme's voice is warm, plain and helpful.

## 2. Color Palette

### 2.1 Core Tokens

| Token | Hex | Use |
|---|---|---|
| `--acme-ink` | `#1B2A41` | Text on light surfaces |
| `--acme-paper` | `#FAF7F2` | Light surface |
| `--acme-night` | `#0B1220` | Dark surface |
| `--acme-chalk` | `#F2EFE8` | Text on dark surfaces |
| `--acme-coral` | `#B23A22` | Accent and buttons |

### 2.5 Accessibility Rules (HARD)

- Body text minimum contrast ratio: **4.5:1** against its surface.

## 3. Typography

### 3.1 Font Stack

```css
--font-sans: "Lato", Arial, sans-serif;
```

```css
.pull-quote { font-family: "Playfair Display", serif; }
```

### 3.2 Scale

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `--fs-h1` | 2.5rem | 700 | 1.15 | 0 | Section title |
| `--fs-h1` | 3.25rem | 700 | 1.15 | 0 | Hero title |
| `--fs-h2` | 1.75rem | 700 | 1.2 | 0 | Sub-section title |
| `--fs-body` | 1rem | 400 | 1.6 | 0 | Body copy |

### 3.3 Style Rules

- **Body copy**: Regular (400), line-height 1.6, color (`--acme-ink` on light, `--acme-chalk` on dark).

## 7. Components

### 7.1 Buttons

| Variant | Background | Text | Border | Hover | Use |
|---|---|---|---|---|---|
| **Primary (CTA)** | `--acme-coral` | `--acme-paper` | none | darken 8% | Primary action |

## 10. Do's & Don'ts (Hard Rules)

| ✓ Do | ✗ Don't |
|---|---|
| Default surface is `--acme-paper` | Make the entire site dark |
| Use Lato exclusively | Mix in other typefaces |
