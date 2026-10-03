# Design System Document: Industrial Precision

## 1. Overview & Creative North Star: "The Kinetic Blueprint"
This design system is a rejection of the "soft" web. For a Data Engineer portfolio, we are moving away from friendly roundness and toward **Industrial Brutalism**. The Creative North Star is **"The Kinetic Blueprint"**—a visual language that feels like a live technical schematic. It is high-precision, authoritative, and unapologetically technical.

To break the "template" look, we utilize **Intentional Asymmetry**. Rather than centering content, we anchor elements to a rigid, visible grid, leaving large "technical voids" (negative space) that suggest room for data expansion. Overlapping elements—such as a monospace label bleeding over a container edge—communicate a "work-in-progress" engineering aesthetic that feels custom and high-end.

---

## 2. Colors & Surface Logic
The palette is rooted in the "Cold Steel" spectrum, punctuated by a high-energy `primary_container` (#FF571A) that mimics a warning light or a critical data point.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. They create visual "stutter." Instead, boundaries are defined through **Background Tonal Shifts**. Use `surface` as your base and `surface_container_low` for secondary sections. The eye should perceive the change in depth through color, not a stroke.

### Surface Hierarchy & Nesting
Treat the UI as a series of machined metal plates.
*   **Base:** `background` (#111316)
*   **Layer 1:** `surface_container_low` (Main content blocks)
*   **Layer 2:** `surface_container_high` (Interactive cards or code snippets)
*   **Nesting:** Place a `surface_container_lowest` element inside a `surface_container_highest` block to create an "etched" or "recessed" look, simulating physical precision-milled components.

### The "Glass & Gradient" Rule
While the system is industrial, it must not feel "flat." 
*   **CTAs:** Use a linear gradient from `primary` (#FFB59E) to `primary_container` (#FF571A) at a 135-degree angle to give buttons a "glow-discharge" effect.
*   **Floating Panels:** Use `surface_variant` with a 60% opacity and a `20px` backdrop-blur to create a "technical glass" overlay, allowing the underlying grid to remain visible.

---

## 3. Typography: The Engineering Spec
Typography must be used to create an editorial hierarchy that mirrors a technical manual.

*   **Display & Headlines (Space Grotesk):** These are your "Structural Identifiers." Use `display-lg` with tight letter-spacing (-0.02em) to command authority. Headlines should be used asymmetrically—often tucked into the top-left of a container.
*   **Technical Detail (Inter):** Use for body copy. It is the "Instruction Manual" of the site.
*   **The Monospace Utility:** Although not in the token list, all data points, timestamps, and "metadata" should be set in a crisp monospace font (like JetBrains Mono or Roboto Mono) using the `label-sm` scale to reinforce the Data Engineering context.

---

## 4. Elevation & Depth: Tonal Layering
In this system, we do not "drop shadows"; we "emit light."

*   **The Layering Principle:** Depth is achieved by stacking. A `surface_container_highest` card sitting on a `surface` background provides all the "lift" required. 
*   **Ambient Shadows:** If a floating element (like a modal) is necessary, use an extra-diffused shadow: `box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5)`. The shadow color is never grey; it is a darker version of the `background`.
*   **The "Ghost Border" Fallback:** For accessibility in forms, use the `outline_variant` token at **15% opacity**. This creates a "phantom" edge that defines the space without cluttering the technical aesthetic.
*   **The Grid Background:** Implement a subtle 24px or 48px grid pattern using `outline_variant` at 5% opacity. This acts as the "drafting paper" for the entire experience.

---

## 5. Components

### Buttons (The "Actuator")
*   **Primary:** Sharp corners (`0px`), `primary` background, `on_primary` text. On hover, transition to a `tertiary` glow.
*   **Secondary:** `surface_container_high` background with a `ghost border`. 
*   **Interaction:** On click, use a 2px "inset" shift to simulate a mechanical press.

### Cards & Lists (The "Data Modules")
*   **Forbid Dividers:** Do not use horizontal lines between list items. Use a 4px vertical gap and a subtle background shift (`surface_container_low` vs `surface_container_lowest`) on hover.
*   **Status Chips:** Use `tertiary` (Electric Cyan) for "Active" and `error` for "System Failure." Chips must be rectangular with 0px border-radius.

### Input Fields (The "Parameter Inputs")
*   **Style:** Background `surface_container_lowest`, no borders except for a 2px bottom-accent in `outline_variant`. 
*   **Focus State:** The bottom accent shifts to `primary` (#FFB59E).

### Technical Breadcrumbs
Instead of standard arrows, use forward slashes `/` in `secondary` and monospace type to mimic file paths (e.g., `root / projects / data_pipeline`).

---

## 6. Do's and Don'ts

### Do:
*   **Embrace the Grid:** Align elements to a strict column grid. Let the grid lines be felt, if not always seen.
*   **Use High Contrast:** Place `tertiary` (Cyan) elements against the `surface_dim` background for maximum "OLED" pop.
*   **Type Hierarchy:** Use `label-sm` in all-caps for technical metadata (e.g., "BUILD: SUCCESSFUL").

### Don't:
*   **Never Round Corners:** Even a 2px radius destroys the "Precision" brand. Everything must be 0px.
*   **Avoid Soft Gradients:** No "sunset" or "organic" fades. Gradients should be high-contrast or used to simulate "backlit" hardware.
*   **No Standard Icons:** Avoid "friendly" rounded icons. Use thin-stroke (1px or 1.5px), sharp-angled technical icons.

---

## Director's Final Note
This system succeeds when it feels like a **terminal interface for a high-value asset**. Every pixel should feel like it was placed there for a functional reason. If an element doesn't serve to communicate data or structure, remove it. Precision is the ultimate luxury.