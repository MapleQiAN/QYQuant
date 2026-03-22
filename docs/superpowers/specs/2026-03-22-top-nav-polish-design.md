# Top Navigation Polish Design

## Summary

Polish the existing top navigation in the frontend without changing information architecture, route behavior, or the product's primary color system. The goal is to make the header feel more professional and terminal-like by tightening spacing, reducing softness, and unifying the visual language across the logo area, navigation links, search input, utility buttons, and user avatar cluster.

## Goals

- Preserve the current top-level layout: logo on the left, navigation in the center, utility actions on the right.
- Keep the current primary color palette, but reduce how much area the accent color occupies.
- Shift the header from a soft "generic dashboard" feel to a more restrained financial-product feel.
- Improve visual consistency across component sizing, corner radius, border treatment, hover states, and active states.
- Ensure the top bar still reads clearly at desktop and medium-width breakpoints.

## Non-Goals

- No changes to route structure, navigation ordering, or labels.
- No changes to page-level layout outside the top navigation shell.
- No introduction of new header features, dropdowns, or user actions.
- No brand refresh or primary color replacement.
- No functional changes to profile loading, help panel opening, notifications, or onboarding highlighting.

## Current Problems

The current top bar works functionally, but several visual decisions pull it in different directions:

- The sticky glass container feels softer and more decorative than the surrounding product surfaces.
- Navigation links, search input, utility buttons, and avatar cluster do not fully share the same shape language.
- Active and hover states rely too heavily on the accent color, which makes the header feel more like a generic SaaS admin panel than a focused trading workspace.
- Spacing and corner radii are slightly too relaxed for the intended "professional terminal" direction.
- The right-side utility area looks like separate floating controls rather than one cohesive header system.

## Design Direction

### Overall Tone

Use the existing structure and brand colors, but make the header denser, calmer, and more intentional:

- Slightly reduce softness in rounded corners.
- Use clearer borders and lighter shadows.
- Treat the header as one integrated workspace bar instead of several independent pills.
- Reserve stronger accent treatment for active navigation state and focus feedback only.

### Header Container

The top bar remains sticky and translucent, but its surface treatment becomes steadier:

- Keep a subtle translucent background so the current app style still feels familiar.
- Replace the softer floating-glass impression with a more stable panel treatment.
- Sharpen the border and reduce shadow weight.
- Keep the existing max-width layout and general horizontal structure.

### Logo Cluster

The logo content remains the same, but its framing becomes more disciplined:

- Keep the existing logo image and product name.
- Tighten spacing between the logo mark and wordmark.
- Align logo sizing more closely with the height rhythm used by the navigation and tools.
- Avoid adding extra label text or new decorative branding.

### Navigation Group

The navigation should feel like one grouped control rather than separate floating tabs:

- Retain the current links and ordering.
- Reduce corner radius on links compared to the current version.
- Make default state quieter by relying on text hierarchy and subtle background only on hover.
- Use a restrained active state: shallow accent background, stronger text/icon color, and clearer visual containment.
- Unify icon and label alignment so the icon supports the label instead of competing with it.

### Search Input

The search input should feel like a tool input, not a rounded consumer-style chip:

- Keep the current search behavior and placeholder.
- Slightly reduce pill softness by tightening radius.
- Use a clearer border and calmer focus ring.
- Keep enough width for usability, but allow it to shrink earlier on narrower viewports.
- Align the input height visually with icon buttons and the avatar trigger.

### Utility Buttons

Help and notification buttons should feel like members of the same control family:

- Standardize width, height, border, radius, and hover treatment.
- Keep them visually secondary to the active navigation link.
- Improve notification badge placement and scale so it feels anchored rather than floating.
- Preserve current click behavior.

### Avatar Cluster

The user avatar area should read as a single account entry point:

- Keep avatar initial and level badge.
- Reduce excess visual competition between avatar fill, container background, and level chip.
- Align the cluster height and radius with nearby controls.
- Make hover state feel consistent with other right-side controls.
- Do not add a dropdown, menu, or new account interaction as part of this change.

## Responsive Behavior

The implementation should remain layout-preserving while becoming more resilient on medium widths:

- Treat medium width as the range between `768px` and `1024px`.
- Keep the same three-part structure as long as practical.
- Shrink search width before collapsing spacing elsewhere.
- Allow the search field to reduce progressively from its desktop width down to a minimum usable width of about `160px` within the medium-width range.
- Reduce horizontal gaps in the header before risking overlap.
- Preserve readable navigation labels and avoid creating a cramped or stacked look at medium widths.

## Implementation Scope

Primary files expected:

- `frontend/src/components/TopNav.vue`
- `frontend/src/styles/global.css`
- `frontend/src/App.vue` if the surrounding shell needs a tiny adjustment for visual cohesion

Implementation should stay mostly within styling and lightweight template adjustments in `TopNav.vue`. Functional logic should remain untouched unless a markup refinement is needed to support the visual grouping cleanly.

## Interaction and State Rules

- Hover states should be present but understated.
- Focus styles must remain visible for keyboard users.
- Active navigation state should be clearly distinguishable without becoming a loud solid block.
- Onboarding highlight behavior must continue to work with the revised navigation styling.
- Sticky positioning and layering must continue to behave above page content.

## Testing Strategy

Testing should focus on preventing behavioral regressions while validating the visual-shell changes safely:

- Run the frontend unit tests that cover routing and top-level app shell behavior if any are affected.
- Add or update a focused component test only if markup changes alter classes, accessible labels, or rendered structure in a meaningful way.
- Perform manual verification in the browser for:
  - default header state
  - hover and active navigation states
  - search focus state
  - notification badge placement
  - medium-width layout behavior
  - onboarding highlight visibility

## Acceptance Criteria

- The top navigation looks like one cohesive system rather than separate visual islands.
- The header feels more professional and terminal-like without changing the current primary color system.
- Navigation, search, buttons, and avatar share a more consistent shape and sizing language.
- Active and hover states are clearer and more restrained than before.
- No navigation behavior, route wiring, or utility interactions regress.
- The result remains stable across desktop and medium-width layouts.
