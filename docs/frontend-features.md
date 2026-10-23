# Frontend features (GUI)

Everything here is something the animator sees or clicks, built in `gui/`. The work behind each screen (reading `.kra` files, storing history, merging, syncing) is in [backend-features.md](backend-features.md), and the search AI is in [ai-features.md](ai-features.md). The **Needs from backend** column names the backend task each screen depends on, so a screen can be built against `fake_backend.py` while the backend is still being written.

The old section B (reading and writing `.kra` files) and the L4 safe-writes item are backend-only and now live in the backend list as KR1 to KR6 and RP6.

Priority: P0 = needed for a working product, P3 = nice to have. Put the owner's name in the Name column.


## A. Project setup

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| A1 | New project screen | Pick a .kra file, enter the author name, and create the project. Show clearly if the folder already has a project | RP1 | P0 |  |
| A2 | Open project screen | Choose a project folder, or pick from the recent-projects list | RP2 | P0 |  |
| A3 | Clone screen | Paste the project's server address, sign in, choose a folder, and show download progress | SY10, SY1 | P1 |  |
| A4 | Project settings screen | Show the folder path, author name, server address, and signed-in account, and let the animator change them | RP3 | P1 |  |
| A5 | Ignore rules editor | Show which files are skipped (such as file.kra~) and let the animator add to the list | RP4 | P1 |  |
| A6 | Relink screen | When the .kra can't be found, ask the animator to locate it | RP5 | P2 |  |

## C. Commit

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| C1 | Changes view | List the layers changed since the last commit, each marked added, removed, redrawn, renamed or settings changed | HI1 | P0 |  |
| C2 | Commit box | Note field and Commit button, with a clear success or failure message. Keyboard shortcut to commit | HI2 | P0 |  |
| C3 | Unsaved-work warning | Banner reminding the animator to save in Krita first when the file looks older than their last session | HI8 | P2 |  |
| C4 | Edit note | Let the animator edit a commit's note afterward | HI9 | P3 |  |

## D. Timeline

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| D1 | Timeline sidebar | List commits with thumbnail, time, author, and note, newest first. Thumbnails have text alternatives | HI3, HI4 | P0 |  |
| D2 | Version preview | Click a commit to see a larger preview and its changed layers | HI3, HI4 | P0 |  |
| D3 | Filters | Filter by author, branch, layer, or date | HI3 | P2 |  |
| D4 | Branch graph | Draw how branches split and merge | BR4 | P2 |  |

## E. Compare

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| E1 | Side-by-side view | Show two versions next to each other, zoom and pan together | HI4 | P0 |  |
| E2 | Overlay slider | Drag a slider to sweep between two versions, with keyboard control of the slider | HI4 | P0 |  |
| E3 | Layer differences list | List the layers that differ between the two versions | HI5 | P1 |  |
| E4 | Highlight changed areas | Mark the regions that changed on the picture | HI6 | P2 |  |

## F. Restore

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| F1 | Restore button | Ask the animator to confirm, then show where the restored .kra was written. Explain that the current version stays in history | HI7 | P0 |  |
| F2 | Damaged-version message | If the version is damaged, say what is wrong and offer the nearest good version | HI7, RP7, IF2 | P0 |  |
| F3 | Open in Krita | Button that opens the restored file in Krita | (none: the app launches Krita) | P2 |  |

## G. Branches

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| G1 | New branch dialog | Name a branch and start it from any version | BR1 | P0 |  |
| G2 | Switch branch | Choose a branch, with a warning first if there are uncommitted changes | BR2 | P1 |  |
| G3 | Rename or delete | Tidy up branches, with confirmation | BR3 | P3 |  |
| G4 | Remote branches | List the branches on the server, including teammates', and preview them | SY4 | P1 |  |

## H. Search (AI)

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| H1 | Search box | Type a description like "when I changed the hair" | ai AI5 | P1 |  |
| H2 | Results list | Show ranked matches with preview, time, and layers | ai AI5, AI9, AI13 | P1 |  |
| H3 | Result check | The animator must answer "Is this the one? Yes / No" before anything is restored. Search never changes anything | ai AI11, AI12 | P1 |  |
| H4 | Offline mode setting | Choose the on-computer model and show whether it is ready | ai AI10 | P2 |  |

## I. Sharing

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| I1 | Sign-in screen | Server address, username, password, and a clear connected or not-connected status | SY1 | P0 |  |
| I2 | Publish project | Button to put the project on the server and show its address to send to teammates | SY2 | P0 |  |
| I3 | Push | Button with progress and a result message | SY3 | P0 |  |
| I4 | Pull | Button with progress, and a clear message when a merge is needed | SY4 | P0 |  |
| I5 | Rejected-push help | If the branch has moved, explain in plain words and guide the animator: pull, merge if needed, push again | SY5 | P1 |  |
| I6 | Progress and retry | Progress bar for uploads and downloads, and a Retry button if the connection drops | SY6, IF3 | P1 |  |
| I7 | Ahead/behind indicator | Show how many commits can be pushed and pulled | SY7 | P1 |  |
| I8 | Team members screen | See who has access. Owners can invite or remove people and set read or write | SY8 | P1 |  |
| I9 | Team activity | List who pushed what and when | SY8 | P2 |  |
| I10 | Offline banner | Show when there is no connection and list what is waiting to be pushed | SY9 | P1 |  |

## J. Merge

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| J1 | Merge screen | Pick two branches to combine | MG1, MG2 | P0 |  |
| J2 | Automatic merge result | Show what was combined when different layers changed | MG3 | P0 |  |
| J3 | Conflict screen | If both changed the same layer, show both in the comparison view and let the animator choose, or keep both as separate layers | MG2, MG4, MG6 | P0 |  |
| J4 | Merge preview | Show the result before it is committed | MG5 | P1 |  |
| J5 | Layer notes | Optional "I'm working on Hair" labels, stored on the server, that warn but never lock | server S8 | P2 |  |

## K. Accessibility and errors

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| K1 | Colour contrast | Text and controls meet 4.5:1 (3:1 for large text) | (none) | P0 |  |
| K2 | Text size | Text scales to 200% without breaking the layout | (none) | P0 |  |
| K3 | Consistent navigation | Same order everywhere: Timeline, Compare, Search, Branch, Restore | (none) | P0 |  |
| K4 | Keyboard use | Everything reachable without a mouse | (none) | P1 |  |
| K5 | Clear errors | One error dialog used everywhere: what went wrong and what to do next, using the message the backend sends | IF2 | P0 |  |

## L. App behaviour (GUI side)

| ID | Feature | What the screen does | Needs from backend | Priority | Name |
|---|---|---|---|---|---|
| L1 | Background work | Every backend call runs off the screen thread with a progress bar, so the window never freezes | IF3, IF4 | P0 |  |
| L2 | Recent projects and settings | Remember recent projects, server address, author name, and text size between sessions | (none) | P1 |  |
| L3 | Check project button | Run the repository check and show what is wrong in plain words | RP7 | P1 |  |

## Notes

- Screens only call functions listed in `backend_api.py`. They never read files or call the server themselves.
- Until the backend exists, every screen runs on `fake_backend.py`. Make the fake take a moment and sometimes fail, so progress bars and error messages get built and tested.
- A1: the project's `.anigit/` folder is created in the same folder as the `.kra`.
- Accessibility (K1 to K4) applies to every screen from the start. It is hard to add afterwards.
