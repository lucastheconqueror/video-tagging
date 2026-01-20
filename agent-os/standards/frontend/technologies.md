# Frontend Technologies & Standards

## Core Stack
- **Framework:** React / Next.js (Infer from project context)
- **Styling:** Tailwind CSS
- **UI Library:** shadcn/ui
- **Theming:** tweakcn (CSS variables)

## Component Installation Rules
**Strictly follow this workflow for adding new UI components:**

1.  **CLI Only:** Never manually copy-paste component code. Always use the CLI to ensure dependencies and utilities are correctly configured.
    *   **Command:** `npx shadcn@latest add <component-name>`
    *   *Note: Do not use "npx install shadcn"; use the `add` command specifically.*
2.  **Target Directory:** All shadcn components must reside in the `ui` folder (e.g., `components/ui` or `src/components/ui` depending on `components.json` configuration).
3.  **No Overwrites:** If a component already exists, check if it needs modification before overwriting.

## Styling & Theming (TweakCN)
- **Theme Source:** Use [tweakcn](https://tweakcn.com) to generate or reference base styles.
- **Implementation:**
    - Do not hardcode hex colors in Tailwind classes.
    - Use CSS variables derived from the TweakCN export (e.g., `bg-primary`, `text-muted-foreground`).
    - Ensure `globals.css` (or equivalent) reflects the TweakCN color palette variables.

## Component Selection Strategy
- **"Best Component for the Job":**
    - Evaluate the user requirement against the available shadcn library first.
    - **Example:** If the user needs a dropdown, strictly use `dropdown-menu`. If they need a select input, use `select`. Do not build custom primitives if a shadcn equivalent exists.
    - **Composition:** Combine atomic shadcn components to build complex UIs (e.g., use `card`, `avatar`, and `badge` together for a profile view) rather than writing raw HTML/Tailwind.

## Best Practices
- **Tailwind:** Use utility classes for layout and spacing. Avoid custom CSS files unless modifying animation keyframes.
- **Icons:** Use `lucide-react` (standard with shadcn) for all iconography.
- **Clean Code:** Run linter after installing components to ensure imports match project aliases (e.g., `@/components/ui/...`).

