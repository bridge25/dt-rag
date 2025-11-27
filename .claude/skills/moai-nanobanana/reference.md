# Nano Banana Pro - Reference

## CLI Installation & Setup

### Prerequisites

```bash
# Node.js 20+ required
node --version  # Should be >= 20.0.0

# Install Gemini CLI globally
npm install -g @google/gemini-cli

# Install Nanobanana extension
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana
```

### Authentication

```bash
# Option 1: Google Account (Free tier: 60 req/min, 1000 req/day)
gemini  # Follow prompts to authenticate

# Option 2: API Key
export GOOGLE_API_KEY=your_api_key_here
```

### Model Selection

```bash
# Default: Nano Banana (gemini-2.5-flash-image)
# Resolution: 1024px, Cost: ~$0.039/image

# Pro Model: Nano Banana Pro (gemini-3-pro-image-preview)
export NANOBANANA_MODEL=gemini-3-pro-image-preview
# Resolution: up to 4K, Cost: ~$0.13-0.24/image
```

---

## CLI Commands Reference

### /generate - Create New Images

```bash
# Basic generation
/generate "a modern dashboard UI with dark theme"

# Multiple variations
/generate "login page wireframe" --count=3

# With preview (opens in viewer)
/generate "settings panel mockup" --preview

# High resolution (Pro only)
/generate "hero section design" --resolution=4k
```

### /edit - Modify Existing Images

```bash
# Basic edit
/edit mockup.png "change the background to dark blue"

# Add elements
/edit wireframe.png "add a navigation sidebar on the left"

# Style transfer
/edit screenshot.png "convert to flat design style"
```

### /restore - Fix Damaged Images

```bash
# Restore old/damaged image
/restore old_design.jpg

# Enhance low quality
/restore blurry_mockup.png "enhance sharpness"
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NANOBANANA_MODEL` | Model to use | `gemini-2.5-flash-image` |
| `NANOBANANA_OUTPUT` | Output directory | `./nanobanana-output/` |
| `GOOGLE_API_KEY` | API key for authentication | - |

---

## Output Management

### Default Output Structure

```
./nanobanana-output/
├── generate_20251123_143052_001.png
├── generate_20251123_143052_002.png
├── edit_20251123_143215_001.png
└── metadata.json
```

### Custom Output

```bash
# Set custom output directory
export NANOBANANA_OUTPUT=/path/to/assets/

# Or use --output flag
/generate "icon design" --output=/project/assets/icons/
```

---

## Prompt Engineering Reference

### Lighting Keywords (High Impact)

| Keyword | Effect |
|---------|--------|
| `soft ambient lighting` | Even, gentle illumination |
| `dramatic side lighting` | Strong contrast, shadows |
| `backlit silhouette` | Subject outlined against light |
| `studio lighting` | Professional, clean look |
| `neon glow` | Cyberpunk, futuristic feel |

### Style Modifiers

| Style | Description |
|-------|-------------|
| `flat design` | Simple, no shadows |
| `neumorphism` | Soft 3D, subtle shadows |
| `glassmorphism` | Frosted glass effect |
| `brutalist` | Raw, bold typography |
| `minimalist` | Clean, essential elements only |

### Camera/Composition Terms

| Term | Effect |
|------|--------|
| `bird's eye view` | Top-down perspective |
| `isometric` | 3D without perspective |
| `close-up` | Detail focus |
| `wide shot` | Full context view |
| `centered composition` | Subject in middle |

### Negative Prompts (What to Avoid)

```
"... no text artifacts, no blurry edges, no distorted elements,
no watermarks, no hands, no complex text"
```

---

## Resolution & Quality

### Nano Banana (Standard)

- Output: 1024 x 1024 px
- Best for: Quick iterations, concept exploration
- Cost: ~$0.039 per image

### Nano Banana Pro

| Resolution | Dimensions | Cost | Use Case |
|------------|------------|------|----------|
| 1K | 1024 x 1024 | ~$0.13 | Standard mockups |
| 2K | 2048 x 2048 | ~$0.13 | Detailed UI |
| 4K | 4096 x 4096 | ~$0.24 | Production assets |

---

## Rate Limits

### Free Tier (Google Account)

- 60 requests per minute
- 1,000 requests per day
- Switches to standard model after quota

### Paid Tier (Google AI Plus/Pro)

- Higher limits
- Priority access
- Consistent Pro model access

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Extension not found" | Reinstall: `gemini extensions install ...` |
| "Rate limit exceeded" | Wait or upgrade tier |
| "Model unavailable" | Check `NANOBANANA_MODEL` value |
| "Authentication failed" | Re-run `gemini` to re-authenticate |

### Debug Mode

```bash
# Enable verbose logging
export GEMINI_DEBUG=true
gemini
```

---

## Integration with Claude Code

### Agent Invocation Pattern

```python
# In nanobanana-designer agent
gemini "/generate 'dashboard mockup with sidebar navigation, dark theme,
blue accents, flat design style, clean UI'"

# Check output
ls ./nanobanana-output/
```

### Workflow Integration

1. Agent receives UI component request
2. Constructs prompt using Skill patterns
3. Executes via Bash tool: `gemini "/generate ..."`
4. References generated image for implementation

---

## Sources

- [GitHub - gemini-cli-extensions/nanobanana](https://github.com/gemini-cli-extensions/nanobanana)
- [Google Blog - Nano Banana Pro Tips](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/)
- [Google Blog - Nano Banana Pro Launch](https://blog.google/technology/ai/nano-banana-pro/)
