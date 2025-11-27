# Ethereal Glass Robot Avatar Generation - Nano Banana Prompts

## Overview

This document contains detailed Nano Banana prompts for generating 16 Ethereal Glass robot avatars using Google's Gemini API. These prompts are designed to produce PNG versions of the SVG robot avatars with high-quality rendering.

## Prerequisite Setup

Before running any prompts, ensure:

```bash
# 1. Install Gemini CLI (if not already installed)
npm install -g @google/gemini-cli

# 2. Set your Google API key
export GOOGLE_API_KEY="your-api-key-here"

# 3. (Optional) Use Pro model for higher quality
export NANOBANANA_MODEL="gemini-2-flash-exp"
```

## Prompt Structure

Each prompt follows this pattern:

```
"[Robot Name] ethereal glass robot character, 
[Personality trait], [Role description],
[Rarity] tier with [Color] glowing accents,
futuristic AI companion, sleek futuristic design,
dark navy space background (#0b1121),
glass frame border, digital holographic effects,
512x512, transparent PNG background,
studio lighting, high detail, professional quality,
no text artifacts, clean professional look"
```

## Common Tier - Gray/Silver (Subtle Glow)

### 1. Analyst Robot
```bash
gemini "/generate 'Analyst ethereal glass robot character, 
logical analytical personality, data analyst role,
common tier with silver glowing accents,
futuristic AI companion, sleek minimalist design,
dark navy space background (#0b1121),
glass frame border, subtle digital glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 2. Builder Robot
```bash
gemini "/generate 'Builder ethereal glass robot character,
creative constructive personality, constructor role,
common tier with silver glowing accents,
futuristic AI companion, robust mechanical design,
dark navy space background (#0b1121),
glass frame with metallic edges, subtle shimmer,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 3. Explorer Robot
```bash
gemini "/generate 'Explorer ethereal glass robot character,
curious adventurous personality, navigator role,
common tier with silver glowing accents,
futuristic AI companion, streamlined elegant design,
dark navy space background (#0b1121),
glass frame border, subtle energy glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 4. Guardian Robot
```bash
gemini "/generate 'Guardian ethereal glass robot character,
protective defensive personality, guardian role,
common tier with silver glowing accents,
futuristic AI companion, sturdy shield-like design,
dark navy space background (#0b1121),
glass frame border with protective aura,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

## Rare Tier - Cyan/Blue (Moderate Glow)

### 5. Innovator Robot
```bash
gemini "/generate 'Innovator ethereal glass robot character,
bold creative personality, innovator role,
rare tier with cyan glowing accents,
futuristic AI companion, avant-garde dynamic design,
dark navy space background (#0b1121),
cyan glass frame, moderate digital glow effect,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 6. Mentor Robot
```bash
gemini "/generate 'Mentor ethereal glass robot character,
wise guiding personality, mentor guide role,
rare tier with cyan glowing accents,
futuristic AI companion, elegant sage design,
dark navy space background (#0b1121),
cyan glass frame, wisdom light emanation,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 7. Optimizer Robot
```bash
gemini "/generate 'Optimizer ethereal glass robot character,
efficient improving personality, optimization role,
rare tier with cyan glowing accents,
futuristic AI companion, streamlined precise design,
dark navy space background (#0b1121),
cyan glass frame, flowing energy patterns,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 8. Pioneer Robot
```bash
gemini "/generate 'Pioneer ethereal glass robot character,
adventurous exploring personality, explorer role,
rare tier with cyan glowing accents,
futuristic AI companion, trailblazer bold design,
dark navy space background (#0b1121),
cyan glass frame, forward motion energy glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

## Epic Tier - Purple (Prominent Glow)

### 9. Researcher Robot
```bash
gemini "/generate 'Researcher ethereal glass robot character,
intellectual scholarly personality, researcher role,
epic tier with purple glowing accents,
futuristic AI companion, sophisticated scholar design,
dark navy space background (#0b1121),
purple glass frame, mystical knowledge aura,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 10. Strategist Robot
```bash
gemini "/generate 'Strategist ethereal glass robot character,
calculating tactical personality, strategist planner role,
epic tier with purple glowing accents,
futuristic AI companion, geometric strategic design,
dark navy space background (#0b1121),
purple glass frame, tactical mind pattern glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 11. Synthesizer Robot
```bash
gemini "/generate 'Synthesizer ethereal glass robot character,
harmonious integrating personality, synthesis role,
epic tier with purple glowing accents,
futuristic AI companion, flowing harmonic design,
dark navy space background (#0b1121),
purple glass frame, harmony resonance glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 12. Tracker Robot
```bash
gemini "/generate 'Tracker ethereal glass robot character,
precise monitoring personality, tracking observer role,
epic tier with purple glowing accents,
futuristic AI companion, focused sentinel design,
dark navy space background (#0b1121),
purple glass frame, surveillance tracking aura,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

## Legendary Tier - Gold (Intense Glow)

### 13. Validator Robot
```bash
gemini "/generate 'Validator ethereal glass robot character,
critical verifying personality, validator role,
legendary tier with gold glowing accents,
futuristic AI companion, authoritative judge design,
dark navy space background (#0b1121),
gold glass frame, powerful validation aura,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 14. Visionary Robot
```bash
gemini "/generate 'Visionary ethereal glass robot character,
ambitious dreaming personality, visionary role,
legendary tier with gold glowing accents,
futuristic AI companion, transcendent oracle design,
dark navy space background (#0b1121),
gold glass frame, destiny vision bright glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 15. Warden Robot
```bash
gemini "/generate 'Warden ethereal glass robot character,
authoritative overseeing personality, warden overseer role,
legendary tier with gold glowing accents,
futuristic AI companion, majestic guardian design,
dark navy space background (#0b1121),
gold glass frame, authoritative command aura,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

### 16. Wizard Robot
```bash
gemini "/generate 'Wizard ethereal glass robot character,
mysterious enchanting personality, wizard enchanter role,
legendary tier with gold glowing accents,
futuristic AI companion, arcane mystical design,
dark navy space background (#0b1121),
gold glass frame, magical enchantment glow,
512x512, transparent PNG background,
studio lighting, high detail, professional,
no text artifacts, clean professional look'"
```

## Batch Generation Script

Once API is configured, run this script to generate all robots:

```bash
#!/bin/bash
# save as: generate_all_robots.sh

ROBOTS=(
  "Analyst ethereal glass robot character, logical analytical personality, data analyst role, common tier with silver glowing accents, futuristic AI companion, sleek minimalist design, dark navy space background, glass frame border, subtle digital glow, 512x512, transparent PNG, studio lighting, high detail, no text"
  "Builder ethereal glass robot character, creative constructive personality, constructor role, common tier with silver glowing accents, futuristic AI companion, robust mechanical design, dark navy space background, glass frame with metallic edges, subtle shimmer, 512x512, transparent PNG, studio lighting, high detail, no text"
  # ... (add remaining 14 prompts)
)

for i in "${!ROBOTS[@]}"; do
  echo "Generating robot $(($i + 1))/16..."
  gemini "/generate '${ROBOTS[$i]}'"
  sleep 2  # Respect rate limits
done

echo "All robots generated!"
```

## Output Management

After generation, organize the PNG files:

```bash
# Move generated PNGs to proper directory
mv nanobanana-output/*.png apps/frontend/public/avatars/robots/

# Convert SVG to PNG if needed (as fallback)
for svg in apps/frontend/public/avatars/robots/*.svg; do
  convert "$svg" "${svg%.svg}.png"
done
```

## Design Notes

- **All robots** share the Ethereal Glass aesthetic from Phase 1 design
- **Color scheme** varies by rarity (common→rare→epic→legendary)
- **Glow intensity** increases with rarity tier
- **Background** is consistent dark navy (#0b1121) for all
- **Size** is uniform 512x512 for UI consistency
- **Transparency** is critical for card overlays

## API Rate Limits

- Free tier: 60 req/min, 1000 req/day
- Pro tier: Higher limits available
- Batch generation recommended overnight

## Quality Assurance

After generation, verify:
- [ ] All 16 robots generated successfully
- [ ] PNG files have transparency
- [ ] Colors match rarity scheme
- [ ] File sizes are reasonable (< 500KB each)
- [ ] Names are correctly applied
- [ ] Files are in correct directory

## Future Enhancements

- Generate additional variants (poses, expressions)
- Create 4x4 sprite sheets for animation
- Add hover state variants
- Generate 3D model versions
- Create team-colored variants

---

Last Updated: 2025-11-28
