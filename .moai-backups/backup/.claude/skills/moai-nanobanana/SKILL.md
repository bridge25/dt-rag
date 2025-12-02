---
name: moai-nanobanana
version: 1.0.0
created: 2025-11-23
status: active
description: Nano Banana Pro (Gemini 3 Pro Image) prompting patterns for UI mockups, icons, and frontend assets. Use when generating visual assets for frontend development, creating UI wireframes, or producing design references.
keywords: [nanobanana, image-generation, ui-mockup, wireframe, gemini, frontend-assets, icons]
allowed-tools:
  - Bash
  - Read
  - Write
---

# Nano Banana Pro - Frontend Asset Generation

## Skill Metadata

| Field | Value |
| ----- | ----- |
| Version | 1.0.0 |
| Tier | Domain |
| Auto-load | When frontend/UI asset generation is needed |
| CLI | Gemini CLI + Nanobanana Extension |

---

## What It Does

Provides prompting patterns and CLI usage for **Nano Banana Pro** (Gemini 3 Pro Image) to generate frontend development assets: UI mockups, wireframes, icons, and design references.

---

## Quick Start

### Prerequisites

```bash
# Install Gemini CLI
npm install -g @google/gemini-cli

# Install Nanobanana extension
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana

# (Optional) Use Pro model
export NANOBANANA_MODEL=gemini-3-pro-image-preview
```

### Basic Commands

| Command | Purpose |
|---------|---------|
| `/generate "prompt"` | Text-to-image generation |
| `/generate "prompt" --count=3` | Multiple variations |
| `/edit image.png "instruction"` | Edit existing image |
| `/restore photo.jpg` | Restore damaged image |

**Output**: `./nanobanana-output/`

---

## Prompt Formula (Google Official)

```
Subject + Action + Environment + Art Style + Lighting + Details
```

### Elements

| Element | Description | Example |
|---------|-------------|---------|
| **Subject** | Main object/character | "modern dashboard interface" |
| **Action** | What's happening | "displaying real-time analytics" |
| **Environment** | Setting/background | "on a dark themed canvas" |
| **Art Style** | Visual aesthetic | "flat design, minimalist" |
| **Lighting** | Light description | "soft ambient glow from screen" |
| **Details** | Refinements | "with blue accent colors, rounded corners" |

---

## Frontend-Specific Patterns

### UI Mockup Pattern

```
"[Component type] interface for [purpose], [style], [color scheme],
[layout details], clean UI design, no text artifacts"
```

### Icon Generation Pattern

```
"[Icon subject] icon, [style] style, [size]px, [color] on [background],
simple flat design, centered, no text"
```

### Wireframe Pattern

```
"Low-fidelity wireframe of [page type], grayscale,
showing [key elements], minimal detail, sketch style"
```

---

## Best Practices

### Do's
- Be specific: subject, composition, style
- Use film/photography terminology for lighting
- Specify what you DON'T want (negative prompts)
- Include resolution hints: "crisp", "high-detail", "4K"

### Don'ts
- Avoid too many instructions (confuses model)
- Don't expect perfect text rendering
- Avoid vague descriptions: "nice", "good", "beautiful"

---

## Model Comparison

| Model | Code | Resolution | Best For |
|-------|------|------------|----------|
| Nano Banana | `gemini-2.5-flash-image` | 1K | Quick iterations |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | 2K/4K | Production assets |

---

## Related Files

- [reference.md](reference.md) - CLI options, environment variables
- [examples.md](examples.md) - Frontend-specific prompt examples

---

**End of Skill** | Created 2025-11-23
