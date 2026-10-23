# AniGit GUI

The desktop app animators use. It shows the timeline, commits, compares versions, searches,
branches, merges, and shares with the team. All real work (reading `.kra` files, storing history,
merging, syncing) is done by the local backend (`../backend`); the GUI only calls it through
`backend_api.py`.

Feature list and owners: `../docs/frontend-features.md`. The work behind each screen is in `../docs/backend-features.md`.

## Layout

```
src/anigit_gui/
  app.py, main_window.py     start-up and the main window
  backend_api.py             the interface to the backend (the only thing the GUI imports from it)
  fake_backend.py            sample data so screens can be built before the backend exists
  pages/                     one file per screen (welcome, changes, compare, search, branches, share, merge, restore, version_preview)
  timeline/                  the sidebar: list, filters, branch graph
  widgets/                   reusable pieces (overlay slider, side-by-side, layer list, thumbnail, progress bar)
  dialogs/                   new project, clone, settings, errors
  core/                      workers (background jobs), settings, theme, shortcuts, data types
tests/                       accessibility checks (contrast, text size, navigation order) and page tests
```

## Rules

- Pages never read files or call the server directly. They call `backend_api`.
- Anything slow goes through `core/workers.py` so the window never freezes.
- Every error goes through `dialogs/error_dialog.py` (what went wrong + what to do).
- No fixed pixel sizes for text or layouts, so text can scale to 200%.
