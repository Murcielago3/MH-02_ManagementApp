---
name: Architectural Precision
colors:
  surface: '#fcf8fa'
  surface-dim: '#ddd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2f4'
  surface-container: '#f1edef'
  surface-container-high: '#ebe7e9'
  surface-container-highest: '#e5e1e3'
  on-surface: '#1c1b1d'
  on-surface-variant: '#47464c'
  inverse-surface: '#313032'
  inverse-on-surface: '#f4f0f2'
  outline: '#78767d'
  outline-variant: '#c8c5cd'
  surface-tint: '#5d5c74'
  primary: '#00000b'
  on-primary: '#ffffff'
  primary-container: '#1a1a2e'
  on-primary-container: '#83829b'
  inverse-primary: '#c6c4df'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#695d3c'
  on-tertiary: '#ffffff'
  tertiary-container: '#b9aa83'
  on-tertiary-container: '#493f20'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2e0fc'
  primary-fixed-dim: '#c6c4df'
  on-primary-fixed: '#1a1a2e'
  on-primary-fixed-variant: '#45455b'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#f2e1b7'
  tertiary-fixed-dim: '#d5c59d'
  on-tertiary-fixed: '#231b02'
  on-tertiary-fixed-variant: '#514627'
  background: '#fcf8fa'
  on-background: '#1c1b1d'
  surface-variant: '#e5e1e3'
typography:
  h1:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  tabular-nums:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  sidebar-width: 240px
---

## Brand & Style
The design system for Studio MH02 is rooted in the "Functional Minimalist" movement, specifically blending the structural clarity of Enterprise SaaS platforms like Linear with the content-first document hierarchy of Notion. The aesthetic is rigorous, disciplined, and utilitarian, mirroring the precision required in architectural practice. 

The brand personality is authoritative and architectural. It avoids decorative flourishes in favor of structural integrity and information density. The UI should evoke a sense of quiet efficiency and professional reliability, providing a high-utility environment for managing complex projects, blueprints, and data.

## Colors
The palette is dominated by a stark white workspace to maximize legibility and focus. A deep navy sidebar provides a permanent structural anchor, creating a clear mental model between navigation and canvas. 

- **Primary & Sidebar:** #1a1a2e (Dark Navy) is used for the global navigation container and primary text to ensure high contrast.
- **Accent:** #0d9488 (Deep Teal) is used sparingly for interactive states, progress indicators, and primary actions.
- **Neutral/Secondary:** #334155 (Slate Blue) handles secondary text and metadata.
- **UI Borders:** #e2e8f0 (Slate 200) is the workhorse for defining the dense grid without adding visual weight.

## Typography
Inter is the exclusive typeface for this design system, chosen for its exceptional legibility in dense data environments and its neutral, "invisible" character. 

Hierarchy is established through weight and casing rather than significant size shifts. Body text is set at 14px for primary reading and 13px for dense data tables and sidebars. Uppercase labels with slight tracking are used for section headers and KPI descriptors to provide architectural structure to the page. Tabular numbers must be used in all data-heavy contexts to ensure vertical alignment in lists and tables.

## Layout & Spacing
The layout uses a fixed-fluid hybrid model. The sidebar remains fixed at 240px, while the main content area utilizes a fluid grid with a maximum readable width of 1200px for document views and 100% width for dashboard views.

A strict 4px baseline grid is used to maintain density. Padding within components is kept tight (8px to 12px) to allow for more information on screen, mirroring the "compact" modes of modern productivity tools. Whitespace is used not for decoration, but to clearly group related technical data.

## Elevation & Depth
Depth is communicated through **low-contrast outlines** and tonal layering rather than shadows. This design system treats the UI as a series of flat, stacked planes.

- **Level 0 (Base):** White background.
- **Level 1 (Containers/Cards):** Defined by a 1px border (#e2e8f0). No shadow.
- **Level 2 (Popovers/Modals):** A single, very soft, high-diffusion shadow (0px 4px 12px rgba(0,0,0,0.05)) is permitted only to separate overlapping utility layers from the primary canvas.
- **Interactive State:** Hovering over list items or table rows triggers a subtle background color shift to #f8fafc rather than an elevation change.

## Shapes
Following the "Soft" configuration, the design system utilizes a minimal 4px (0.25rem) radius for buttons and input fields. Larger containers and cards maintain this 4px radius to preserve a crisp, technical aesthetic. Interactive elements like tags or chips may use a slightly larger radius, but should never become fully circular or "pill-shaped," as this detracts from the professional tone.

## Components
- **Sidebar Navigation:** Solid #1a1a2e background. Text and icons in 60% opacity white, shifting to 100% white on active state. Active items receive a subtle left-aligned 2px accent-colored border.
- **Striped Tables:** 1px horizontal borders only. Alternate rows use #f8fafc. Headers use the `label-caps` typography style with a subtle bottom border.
- **KPI Cards:** Simple 1px bordered boxes. The metric is featured in H2 weight, with the label in `label-caps` Slate Blue above it. No background colors.
- **Input Fields:** 1px border (#e2e8f0) with a 4px radius. On focus, the border shifts to the Accent Teal with a 0px offset, 2px spread subtle glow. 
- **Buttons:** Primary buttons are Solid Navy or Teal with white text. Secondary buttons use a ghost style (1px border, no fill) to maintain a light visual footprint.
- **Status Badges:** Small, rectangular chips with 2px radius. Use low-saturation background tints with high-saturation text for a sophisticated "enterprise" look.