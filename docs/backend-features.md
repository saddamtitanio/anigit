# Backend features

The backend is the code that runs on the animator's computer and does the real work behind the GUI screens: reading `.kra` files, storing history, comparing, restoring, merging, searching, and syncing with the server. It has no windows. The GUI calls it only through `backend_api.py`.

The screens are listed in [frontend-features.md](frontend-features.md). The **Used by (GUI)** column says which screen tasks each backend task supports, so each piece of work is assigned in one place only.

Priority: P0 = needed for a working product, P3 = nice to have. Put the owner's name in the Name column.


## RP. Repository (local history in .anigit/)

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| RP1 | Create project | Make a hidden .anigit/ in the folder of the .kra and save the first commit. If the folder already has one, say so instead of making a second | A1 | P0 |  |
| RP2 | Open project | Find and load the history for a project folder | A2 | P0 |  |
| RP3 | Project settings | Keep author name, server address and the tracked .kra name in a small settings file | A4 | P1 |  |
| RP4 | Ignore rules | Never track Krita's backup and autosave files (file.kra~) | A5 | P1 |  |
| RP5 | Relink file | Find a moved or renamed .kra again without losing history | A6 | P2 |  |
| RP6 | Safe writes | Write every history file to a temporary name and rename it, so a crash or power cut never leaves a broken file | all saving | P0 |  |
| RP7 | Repository check | Check that every stored file exists and matches its fingerprint, and list what is wrong | L3, F2 | P1 |  |

## KR. Reading and writing .kra files

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| KR0 | Inspect tool (do first) | A small script that unzips a real animated .kra from Krita and lists every file, its size and its fingerprint, so the team can confirm the real layout before building on it | (setup) | P0 |  |
| KR1 | Read a .kra | Open the ZIP and read maindoc.xml (layer list and settings), the layer files (pixels), and the preview image | C1, D2 | P0 |  |
| KR2 | Layer fingerprints | Fingerprint each layer's files. Test first that an unchanged layer gets the same fingerprint after Krita saves again. If not, fingerprint the decoded pixels instead | C1 | P0 |  |
| KR3 | Layer matching | Match layers between versions by their ID from maindoc.xml, so renaming or reordering isn't treated as a new layer | C1, J2 | P0 |  |
| KR4 | File storage | Store each file once, named by its fingerprint, and reuse it when unchanged | C2 | P0 |  |
| KR5 | Write a .kra | Rebuild a valid .kra from stored files (first entry 'mimetype', stored uncompressed). Used by restore, clone, switch branch and merge | F1, G2, J2, A3 | P0 |  |
| KR6 | Open check | Confirm a written .kra opens in Krita (manual test checklist plus a script that re-reads it) | F1 | P1 |  |

## HI. History: commit, log, compare, restore

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| HI1 | Changes since last commit | Compare the current .kra with the last commit and list layers added, removed, redrawn, renamed or changed in settings | C1 | P0 |  |
| HI2 | Commit | Save the version with note, author, time, parent commit and preview. Refuse an empty commit | C2 | P0 |  |
| HI3 | List commits | Return commits for a branch, newest first, with the layers each one changed | D1, D2, D3 | P0 |  |
| HI4 | Preview images | Return a commit's preview image (and the merged image used for comparing) | D1, D2, E1, E2 | P0 |  |
| HI5 | Layer differences | List the layers that differ between two commits | E3 | P1 |  |
| HI6 | Changed areas | Work out which regions of a layer changed between two commits | E4 | P2 |  |
| HI7 | Restore version | Check the version is complete and undamaged, then write it as a new .kra next to the original. Never overwrite the current file or history | F1, F2 | P0 |  |
| HI8 | Unsaved-work check | Tell the GUI if the .kra on disk looks older than the last drawing session | C3 | P2 |  |
| HI9 | Amend note | Change a commit's note afterwards | C4 | P3 |  |

## BR. Branches

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| BR1 | Create branch | Make a named branch from any commit | G1 | P0 |  |
| BR2 | Switch branch | Write out the other branch's .kra. Refuse if there are uncommitted changes, unless told to go ahead | G2 | P1 |  |
| BR3 | Rename or delete branch | Tidy up branches (the main branch can't be deleted) | G3 | P3 |  |
| BR4 | Branch graph data | Return parents of each commit so the GUI can draw splits and merges | D4 | P2 |  |

## MG. Merge

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| MG1 | Find common ancestor | Find the commit two branches both started from | J1 | P0 |  |
| MG2 | Merge plan | Compare base, ours and theirs layer by layer. Different layers changed means automatic. The same layer changed means a conflict. Deleted on one side and edited on the other is also a conflict | J1, J2 | P0 |  |
| MG3 | Build merged .kra | Combine the chosen layers into a new .kra and save it as a commit with two parents. Layers added by the other branch need new file names if they clash | J2 | P0 |  |
| MG4 | Conflict choices | Take the animator's choice (ours or theirs, per layer) and finish the merge | J3 | P0 |  |
| MG5 | Merge preview | Return the merged result as a preview without saving anything | J4 | P1 |  |
| MG6 | Keep both | Keep both versions of a conflicting layer as two separate layers | J3 | P2 |  |

## SR. Search

Moved to [ai-features.md](ai-features.md). The backend only provides the commit data that search reads (HI2, HI3, HI4).

## SY. Sync with the server

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| SY1 | Sign in | Sign in to the server and keep the token safely between sessions | I1 | P0 |  |
| SY2 | Publish project | Create the project on the server from a local one | I2 | P0 |  |
| SY3 | Push | Ask which files the server is missing, upload those, then ask it to move the branch, giving the commit the branch was at when you last synced | I3 | P0 |  |
| SY4 | Fetch and pull | Download new commits and their files by walking back through parents. Move a branch forward only if no merge is needed | I4 | P0 |  |
| SY5 | Rejected push | Return a clear result when the server says the branch moved, so the GUI can guide pull, merge, push | I5 | P1 |  |
| SY6 | Retry and progress | Report progress while uploading and downloading, and retry after a dropped connection without leaving a branch half-updated | I6 | P1 |  |
| SY7 | Ahead/behind | Count commits to push and commits to pull for each branch | I7 | P1 |  |
| SY8 | Members and activity | Call the server for who has access and who pushed what | I8, I9 | P2 |  |
| SY9 | Offline | Do everything except sync with no connection, and remember what is waiting to be pushed | I10 | P1 |  |
| SY10 | Clone | Create a project folder from a server address, download the history, and build the .kra from the latest commit | A3 | P1 |  |

## IF. Interface with the GUI

| ID | Feature | What it does | Used by (GUI) | Priority | Name |
|---|---|---|---|---|---|
| IF1 | Interface definition (do first) | Write down every function the GUI may call and the plain data it gets back, in gui/src/anigit_gui/backend_api.py, so the GUI team and the backend team can work at the same time | all | P0 |  |
| IF2 | Clear errors | Every failure carries what went wrong and what to do next, in plain words, plus a short code | K5 | P0 |  |
| IF3 | Progress reporting | Slow jobs report progress so the GUI can show a bar | L1, I6 | P0 |  |
| IF4 | Safe for background threads | No GUI code inside the backend, and no shared state that breaks when called from a worker thread | L1 | P0 |  |
| IF5 | Fake backend stays in sync | Whenever IF1 changes, update gui/.../fake_backend.py to match, so GUI work and backend work never drift apart | all | P1 |  |

## Order of work

1. **IF1 and KR0 first.** The interface lets GUI and backend teams work in parallel. The inspect tool shows what a real animated `.kra` contains before anything depends on it.
2. **KR1 to KR5 and RP6.** Reading, fingerprinting, storing, and writing `.kra` files safely. Everything else builds on these.
3. **RP1, RP2, HI1 to HI4, HI7.** Create a project, commit, list commits, preview, restore. This is the "crash and go back" story from the design.
4. **BR1, BR2, then MG1 to MG4.** Branches and merge.
5. **SY1 to SY4, then the rest of SY.** Needs the server (`../server`) running.
6. **AI search** (see [ai-features.md](ai-features.md)) can happen any time after commits exist.

## Risks to check early

- **Fingerprints (KR2):** Krita may re-save an unchanged layer with different bytes, which would make every layer look changed. Test with real files before building more.
- **Writing a valid `.kra` (KR5):** if Krita refuses a rebuilt file, restore, switch branch, clone, and merge all fail. Test with real files early.
- **Real file layout (KR0):** the structure inside an animated `.kra` (frame and keyframe files) has not been checked against real files yet.
- **Merged previews:** after a merge, the preview image inside the file is stale until Krita saves it again.
- **Big files:** reading a whole `.kra` into memory may be slow or heavy for long animations, so measure with a realistic project.

## Shared format with the server

A commit is a JSON record with `parents`, `files` (path in the `.kra` to fingerprint), optional `layers`, `preview`, `author`, `note`, `timestamp`. The backend writes it and the server checks it. See `../server/README.md`. If the format changes, change both.
