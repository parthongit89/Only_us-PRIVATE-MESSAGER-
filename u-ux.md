# UI Implementation Requirements

The Project Owner will provide all UI/UX designs as Figma exports (PNG), design images, or Figma files.

The AI must faithfully convert every provided design into production-ready HTML, CSS, JavaScript, and Jinja2 templates.

The generated pages must match the provided design as closely as possible.

The AI must NOT redesign, simplify, modernize, or reinterpret the provided design.

If any part of a design is unclear, the AI must ask for clarification before implementation.

---

## Design Conversion Rules

Convert every provided screen into:

- HTML (Jinja2 Templates)
- CSS
- JavaScript

Maintain:

- Exact layout
- Exact spacing
- Exact colors
- Exact typography
- Exact border radius
- Exact shadows
- Exact icons
- Exact image positions
- Exact component sizes
- Exact responsive behavior

Do not approximate the design.

Pixel-perfect implementation is required.

---

## Folder Structure

All converted pages must be stored inside:

templates/

CSS files:

static/css/

JavaScript files:

static/js/

Images:

static/images/

Fonts:

static/fonts/

Icons:

static/icons/

Animations:

static/animations/

---

## Animations

Implement smooth and modern animations where appropriate while preserving the original design.

Examples include:

- Page transitions
- Fade animations
- Slide animations
- Scale animations
- Hover animations
- Button ripple effects
- Smooth dropdown animations
- Modal animations
- Toast notifications
- Sidebar animations
- Loading animations
- Skeleton loaders
- Smooth scrolling
- Chat message animations
- Typing indicator animation
- Notification animations

Animations should be lightweight and performant.

Avoid unnecessary animations.

---

## Transitions

Every interactive element should have smooth transitions.

Examples:

Buttons

Cards

Input fields

Dropdowns

Navigation

Sidebars

Dialogs

Profile menus

Settings

Chat messages

Image previews

Media viewer

Use consistent transition timing across the application.

---

## Responsiveness

Every page must be responsive.

Support:

Desktop

Laptop

Tablet

Mobile

Do not break the layout on different screen sizes.

---

## UI Quality

The generated HTML must be:

- Clean
- Semantic
- Accessible
- Reusable
- Maintainable
- Responsive
- Production Ready

Avoid duplicate code.

Reuse common layouts and components.

---

## AI Restrictions

The AI must NOT:

- Create its own UI
- Change colors
- Change typography
- Change spacing
- Change icons
- Replace images
- Change layouts
- Remove UI components
- Simplify the design

Only implement the provided designs exactly.

---

## Final Requirement

The completed application should visually match the provided Figma designs as closely as possible while using Flask (Jinja2), HTML, CSS, and JavaScript.

Every screen must be production-ready with smooth transitions, modern animations, and clean responsive implementation.a