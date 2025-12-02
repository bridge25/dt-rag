# Nano Banana Pro - Frontend Examples

## UI Mockup Examples

### Dashboard Interface

```bash
/generate "Modern analytics dashboard interface, dark theme with navy blue
background, showing charts and KPI cards in a grid layout, sidebar navigation
on left, flat design style, soft ambient glow from data visualizations,
rounded corners, blue and cyan accent colors, clean professional UI,
no text artifacts"
```

**Use case**: Initial design reference for admin panels

---

### Login/Auth Page

```bash
/generate "Minimalist login page design, centered card layout on gradient
purple to blue background, email and password input fields with floating
labels, prominent sign-in button, social login options below, glassmorphism
card effect, soft shadows, modern sans-serif typography style, clean UI"
```

**Use case**: Auth flow mockup

---

### Settings Panel

```bash
/generate "Settings page interface, left sidebar with category navigation,
main content area showing toggle switches and dropdown menus, light theme
with subtle gray backgrounds, card-based sections, neumorphism style subtle
shadows, clean organized layout, professional SaaS application look"
```

**Use case**: User preferences UI

---

### Data Table View

```bash
/generate "Data table interface with sortable columns, pagination controls
at bottom, search bar and filter buttons at top, alternating row colors,
checkbox selection column, action buttons on right, clean minimal design,
light theme, professional business application style"
```

**Use case**: List/grid view components

---

## Component Examples

### Navigation Sidebar

```bash
/generate "Vertical navigation sidebar component, dark theme, icons with
labels for each menu item, active state highlighted with accent color,
collapsible sections, user avatar at bottom, flat design, 240px width,
clean modern look"
```

---

### Card Component

```bash
/generate "UI card component variations, showing 4 different card styles:
basic info card, stat card with icon, image header card, action card with
buttons, light theme, soft shadows, rounded 8px corners, clean spacing,
grid layout showcase"
```

---

### Modal Dialog

```bash
/generate "Modal dialog popup design, centered on dimmed background overlay,
header with title and close button, body content area, footer with cancel
and confirm buttons, white background, subtle shadow, rounded corners,
clean professional UI component"
```

---

### Form Elements

```bash
/generate "Form UI components showcase, showing text input, dropdown select,
checkbox group, radio buttons, toggle switch, date picker, file upload area,
all in consistent modern style, light theme, organized grid layout,
clean spacing between elements"
```

---

## Icon Examples

### App Icons

```bash
/generate "Mobile app icon, abstract geometric shape representing data flow,
gradient blue to purple, rounded square iOS style, clean simple design,
centered composition, no text, professional look"
```

---

### UI Icons Set

```bash
/generate "Set of 12 outline UI icons on white background, including: home,
settings, user, search, notification, menu, chart, folder, calendar, message,
download, and help icons, consistent 24px stroke width, minimal style,
dark gray color, organized 4x3 grid"
```

---

### Feature Icons

```bash
/generate "Feature illustration icon, cloud computing concept, isometric
style, blue and white color scheme, simple geometric shapes,
subtle gradient, clean modern design, no background, centered"
```

---

## Wireframe Examples

### Homepage Wireframe

```bash
/generate "Low-fidelity wireframe of a SaaS landing page, grayscale only,
showing hero section with headline placeholder, feature grid with 3 columns,
testimonial carousel area, CTA section, footer with links, sketch style
boxes representing content, no detailed text"
```

---

### Mobile App Wireframe

```bash
/generate "Mobile app wireframe screens, 3 iPhone frames side by side showing:
onboarding screen, main feed view, profile page, grayscale sketch style,
placeholder boxes for images and text, simple navigation bar,
low-fidelity prototype look"
```

---

### Dashboard Wireframe

```bash
/generate "Dashboard wireframe layout, top navigation bar, left sidebar menu,
main content area with 4 metric cards and 2 chart placeholders, grayscale,
simple rectangles and lines, no colors except gray shades, blueprint style"
```

---

## Style Variations

### Dark Theme Variants

```bash
# Cyberpunk style
/generate "Dashboard UI, dark theme, neon cyan and magenta accents,
cyberpunk aesthetic, glowing edges, futuristic tech look"

# Professional dark
/generate "Dashboard UI, dark theme, subtle blue-gray tones,
professional business style, clean minimal design"

# High contrast
/generate "Dashboard UI, pure black background, white and yellow accents,
high contrast accessibility-focused design"
```

---

### Light Theme Variants

```bash
# Clean minimal
/generate "Dashboard UI, light theme, white background with light gray cards,
blue accent color, clean minimal professional style"

# Warm palette
/generate "Dashboard UI, light cream background, warm orange and brown accents,
friendly approachable design, soft shadows"

# Apple-inspired
/generate "Dashboard UI, light theme, San Francisco font style,
subtle gradients, Apple design language, premium feel"
```

---

## Multi-Image Composition

### Device Mockups

```bash
/generate "Responsive design showcase, same dashboard displayed on laptop,
tablet, and phone screens, arranged at angles, dark theme UI,
professional product photography style, soft shadows,
clean white background"
```

---

### Before/After Comparison

```bash
/generate "Split screen UI comparison, left side showing old design with
cluttered layout, right side showing modern clean redesign,
clear visual improvement, professional presentation style"
```

---

## Prompt Refinement Tips

### Starting Point → Refined

**Basic**:
```
"dashboard design"
```

**Refined**:
```
"Modern SaaS analytics dashboard interface, dark navy theme,
top navigation bar with search and notifications, left sidebar with
icon-based menu, main content showing 4 KPI cards in top row and
2 chart widgets below (line chart left, bar chart right),
flat design style with subtle shadows, blue and teal accent colors,
clean professional UI, no text artifacts, 4K resolution"
```

### Adding Constraints

```bash
# For text-heavy designs (Pro model better)
/generate "... ensure all text is legible, use placeholder lorem ipsum style"

# For specific dimensions
/generate "... aspect ratio 16:9, suitable for hero section banner"

# For brand consistency
/generate "... following Material Design 3 guidelines,
using Google's color palette"
```

---

## Output Integration

### Using Generated Assets

```typescript
// Reference generated mockup in React component
// File: ./nanobanana-output/dashboard_mockup_001.png

/**
 * Dashboard component implementation
 * Design reference: ./nanobanana-output/dashboard_mockup_001.png
 *
 * Key elements from mockup:
 * - Dark navy background (#0f172a)
 * - Sidebar width: 240px
 * - Card border-radius: 12px
 * - Accent color: #3b82f6
 */
export const Dashboard: React.FC = () => {
  // Implementation based on mockup
}
```

### Asset Organization

```
./nanobanana-output/
├── mockups/
│   ├── dashboard_v1.png
│   ├── dashboard_v2.png
│   └── dashboard_final.png
├── icons/
│   ├── nav_icons_set.png
│   └── feature_icons.png
├── wireframes/
│   └── homepage_wireframe.png
└── components/
    ├── card_variations.png
    └── form_elements.png
```

---

## Sources

- [Google Blog - 7 Tips for Nano Banana Pro](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/)
- [Atlabs - Ultimate Nano Banana Pro Guide](https://www.atlabs.ai/blog/the-ultimate-nano-banana-pro-prompting-guide-mastering-gemini-3-pro-image)
- [Max Woolf - Nano Banana Prompt Engineering](https://minimaxir.com/2025/11/nano-banana-prompts/)
