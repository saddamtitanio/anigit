# Accessibility requirements

- **Contrast:** 4.5:1 normal text, 3:1 large text (check with `gui/src/anigit_gui/core/theme.py`; tests in `gui/tests/`).
- **Text resizing:** up to 200% without layout breakage; use layouts, no fixed pixel sizes.
- **Navigation:** consistent order: Timeline, Compare, Search, Branch, Restore. Full keyboard access.
- **Errors:** say what failed and offer a next step (e.g. corrupted version: explain, offer the previous valid version).
