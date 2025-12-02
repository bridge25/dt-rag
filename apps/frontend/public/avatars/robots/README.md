# Ethereal Glass Robot Avatars

Collection of 16 unique robot character avatars with Ethereal Glass aesthetic for agent profiles.

## Quick Reference

### File Organization

```
robots/
├── [16 robot SVG files]      - Scalable vector graphics
├── robots_index.json          - Metadata and character info
├── NANOBANANA_PROMPTS.md      - PNG generation guide
└── README.md                  - This file
```

### Robot Characters (16 Total)

**Common Tier** (4): Analyst, Builder, Explorer, Guardian
**Rare Tier** (4): Innovator, Mentor, Optimizer, Pioneer
**Epic Tier** (4): Researcher, Strategist, Synthesizer, Tracker
**Legendary Tier** (4): Validator, Visionary, Warden, Wizard

## Usage

### Import Metadata

```javascript
import robotsIndex from './robots_index.json';

const analyst = robotsIndex['Analyst'];
// {
//   "file": "analyst.svg",
//   "personality": "Logical",
//   "role": "Data Analyzer",
//   "rarity": "common",
//   "color_scheme": "#a0a0a0"
// }
```

### Display Robot Image

```html
<img 
  src="/avatars/robots/analyst.svg" 
  alt="Analyst - Data Analyzer"
  className="robot-avatar rarity-common"
/>
```

### CSS Classes

```css
.rarity-common { /* Gray/silver theme */ }
.rarity-rare { /* Cyan/blue theme */ }
.rarity-epic { /* Purple theme */ }
.rarity-legendary { /* Gold theme */ }
```

## Design Features

- **Format**: SVG (scalable to any size)
- **Dimensions**: 512x512 viewport
- **Background**: Transparent
- **Effects**: Gradients, glow, glass morphism
- **Color Scheme**: Rarity-based palettes

## PNG Generation (Optional)

To generate high-quality PNG versions using Google's Gemini API:

1. See `NANOBANANA_PROMPTS.md` for detailed prompts
2. Ensure `GOOGLE_API_KEY` environment variable is set
3. Run generation commands using Gemini CLI
4. PNGs will be output to `nanobanana-output/` directory

## Properties Per Robot

```typescript
interface RobotCharacter {
  file: string;              // Filename (e.g., "analyst.svg")
  personality: string;       // Personality trait
  role: string;              // Robot role/function
  rarity: string;            // Rarity tier (common|rare|epic|legendary)
  color_scheme: string;      // Primary color hex code
}
```

## Color Palettes

### Common Tier
- Primary: #808080
- Accent: #c0c0c0
- Glow: #ffffff

### Rare Tier
- Primary: #0099cc
- Accent: #00d9ff
- Glow: #00d9ff

### Epic Tier
- Primary: #6600cc
- Accent: #b366ff
- Glow: #b366ff

### Legendary Tier
- Primary: #cc9900
- Accent: #ffd700
- Glow: #ffed4e

## Robot Details

| Name | Personality | Role | Rarity | Color |
|------|-------------|------|--------|-------|
| Analyst | Logical | Data Analyzer | common | #a0a0a0 |
| Builder | Creative | Constructor | common | #b0b0b0 |
| Explorer | Curious | Navigator | common | #9a9a9a |
| Guardian | Protective | Defender | common | #aaaaaa |
| Innovator | Bold | Innovator | rare | #00d9ff |
| Mentor | Wise | Guide | rare | #00bfff |
| Optimizer | Efficient | Improver | rare | #00e5ff |
| Pioneer | Adventurous | Explorer | rare | #00d4ff |
| Researcher | Intellectual | Scholar | epic | #b366ff |
| Strategist | Calculating | Planner | epic | #9d5eff |
| Synthesizer | Harmonious | Integrator | epic | #a855ff |
| Tracker | Precise | Monitor | epic | #c77dff |
| Validator | Critical | Verifier | legendary | #ffd700 |
| Visionary | Ambitious | Dreamer | legendary | #ffed4e |
| Warden | Authoritative | Overseer | legendary | #ffc700 |
| Wizard | Mysterious | Enchanter | legendary | #ffde59 |

## Technical Notes

- SVG files use radial gradients for glow effects
- Gaussian blur filters for soft edges
- Opacity layers for depth perception
- Glass morphism style frame borders
- Each robot is 512x512 pixels

## Integration Examples

### React Component

```tsx
import robotsIndex from './robots_index.json';

interface RobotAvatarProps {
  name: string;
  size?: 'small' | 'medium' | 'large';
}

export function RobotAvatar({ name, size = 'medium' }: RobotAvatarProps) {
  const robot = robotsIndex[name];
  if (!robot) return null;

  return (
    <div className={`robot-avatar robot-${size} rarity-${robot.rarity}`}>
      <img 
        src={`/avatars/robots/${robot.file}`}
        alt={`${name} - ${robot.role}`}
        title={`${robot.personality} ${name}`}
      />
      <span className="robot-name">{name}</span>
    </div>
  );
}
```

### Data Retrieval

```typescript
// Get robot by name
const robot = robotsIndex['Analyst'];

// Get all robots of a rarity
const legendaryRobots = Object.entries(robotsIndex)
  .filter(([_, data]) => data.rarity === 'legendary')
  .map(([name]) => name);

// Get robot by role
const analyzers = Object.entries(robotsIndex)
  .filter(([_, data]) => data.role.includes('Analyzer'))
  .map(([name]) => name);
```

## Asset Specifications

- **Format**: SVG with transparency
- **Scalable**: Yes, renders at any resolution
- **Responsive**: Yes, maintains aspect ratio
- **Performant**: ~3.5 KB per file
- **Browser Support**: All modern browsers
- **Accessibility**: Includes alt text and titles

## Next Steps

1. Use robots in agent profile cards
2. Implement rarity-based styling
3. Add hover and interaction effects
4. Consider PNG variants for static contexts
5. Create sprite sheets for animation

---

**Created**: 2025-11-28  
**Format**: SVG (Scalable Vector Graphics)  
**Aesthetic**: Ethereal Glass  
**Total Assets**: 16 robots + metadata
