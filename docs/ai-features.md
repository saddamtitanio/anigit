# AI features

The AI is used for one job only: **searching** the project history from a description in everyday words, such as "find when I changed the hair". It never saves, restores, branches, merges, or changes anything. Every result is checked by the animator (the human-in-the-loop step from the design) before anything happens.

The search screens are in [frontend-features.md](frontend-features.md) (section H) and the surrounding history code is in [backend-features.md](backend-features.md). This file covers what is specific to the AI: the data it reads, the model, the ranking, the safety rules, and how well it works.

Priority: P0 = needed for a working product, P3 = nice to have. Put the owner's name in the Name column.


## DA. Data and model

| ID | Feature | What it does | Works with | Priority | Name |
|---|---|---|---|---|---|
| AI1 | Text for each version | Build a short line of text for every commit from its note, author, changed layer names, and the kind of change (redrawn, renamed, added). This is all the search reads | backend HI2, HI3 | P1 |  |
| AI2 | Colour words (optional) | Describe the main colours of each changed layer in words, such as "dark brown" or "blue", and add them to the text. Without this the search cannot match "when the hair was brown", because it never sees the picture | backend HI4 | P2 |  |
| AI3 | Choose and test the model | Pick a small text-embedding model that runs on an ordinary laptop with no graphics card. Check its licence and download size, and test it on the languages the animators actually write notes in (for example English and Indonesian) | (none) | P1 |  |
| AI4 | Build and update the index | Turn each commit's text into numbers once, when the commit is created or pulled, and keep them in .anigit/. The index is not shared and can always be rebuilt from the commits | backend RP1, SY4 | P1 |  |

## RK. Searching and ranking

| ID | Feature | What it does | Works with | Priority | Name |
|---|---|---|---|---|---|
| AI5 | Rank the results | Compare the animator's words with every commit's text and return the best matches with scores | frontend H1, H2 | P1 |  |
| AI6 | Layer-name boost | If the words match a layer name exactly ("Hair"), rank those commits higher, so obvious matches are never beaten by vague ones | frontend H2 | P1 |  |
| AI7 | Time and order words | Understand phrases like "yesterday", "a few commits ago", or "before the background change" by filtering or boosting using commit time and order | backend HI3 | P2 |  |
| AI8 | No good match | If even the best score is low, say so and suggest browsing the timeline, instead of showing weak guesses. Set the cut-off from the test in AI14 | frontend H2 | P1 |  |
| AI9 | Explain each match | For every result, say why it matched in plain words ("layer: Hair, note: Hair recolour"), so the animator can judge it quickly | frontend H2, H3 | P1 |  |

## SF. Safety and human check

| ID | Feature | What it does | Works with | Priority | Name |
|---|---|---|---|---|---|
| AI10 | Runs on the animator's computer | The model and index live locally. No notes, layer names or artwork are sent to any outside service. Show whether the model is ready and handle the first download | frontend H4 | P1 |  |
| AI11 | Read-only guarantee | Search can only read. It cannot commit, restore, branch, merge, or push. Add a test that fails if search code can reach any of those | frontend H3 | P0 |  |
| AI12 | Human check before any action | The AI only proposes. The GUI asks "Is this the one? Yes / No". Only a Yes leads to any action, and that action is the ordinary restore, a separate call. The screen can never skip the question | frontend H3, F1 | P0 |  |
| AI13 | Label results as suggestions | Every result is marked as an AI suggestion, with its score, so it is never mistaken for a fact | frontend H2 | P1 |  |
| AI14 | Remember Yes and No (optional) | Keep the animator's answers on their computer so accuracy can be measured. Never sent anywhere without asking | AI12 | P2 |  |

## QA. Quality and reliability

| ID | Feature | What it does | Works with | Priority | Name |
|---|---|---|---|---|---|
| AI15 | Test set | Write about 50 realistic questions ("find when I changed the hair") with the known right answer, on one or two sample projects. Measure how often the right version is first, and in the top three. Use this to pick the model (AI3) and the cut-off (AI8) | (none) | P1 |  |
| AI16 | Speed and size | Search should answer in about a second for around 1,000 commits on an ordinary laptop. Measure it, and measure how big the index gets | AI4, AI5 | P1 |  |
| AI17 | Failures | Clear messages when the model is missing, the index is out of date, or there are no commits yet, with what to do next | frontend K5, backend IF2 | P1 |  |
| AI18 | Empty notes | Many commits will have short or empty notes. Test how well search works from layer names alone, and encourage a note when committing | frontend C2 | P2 |  |

## DC. Decision needed

| ID | Feature | What it does | Works with | Priority | Name |
|---|---|---|---|---|---|
| AI19 | Versions or single frames? | The design says the animator asks for a frame and it is "placed on the animation grid". Our history stores whole versions of the file. Decide what a result is (a version, or a particular frame inside it) and what placing it means for a GUI that works on saved files: restore as a new .kra, export that frame as an image, or insert it into the open document (which would need the Krita plugin we dropped) | frontend F1, backend HI7 | P1 (decide) |  |

## How a search works

1. The animator types a description.
2. The words are turned into numbers by the model on their own computer (AI3).
3. Those numbers are compared with the saved numbers for each commit's text (AI1, AI4), and the closest matches are returned with scores and reasons (AI5, AI6, AI9).
4. The screen shows them as AI suggestions with preview, time and layers (AI13, frontend H2).
5. The animator answers Yes or No (AI12). Yes uses the normal restore. No shows the next result.

## Order of work

1. **AI15 and AI3 first.** Write the test questions, then use them to choose the model. Don't pick a model by guessing.
2. **AI1, AI4, AI5.** Text, index, and ranking, enough to get first results.
3. **AI11 and AI12 together with the screen.** The read-only test and the Yes/No step are requirements, not polish.
4. **AI6, AI8, AI9, AI13.** Better ranking, honest "no match" answers, and explanations.
5. **AI10, AI16, AI17.** Local running, speed, and failure messages.
6. **AI2, AI7, AI14, AI18** if time allows.
7. **AI19** needs a decision early, since it changes what the search returns.

## Limits to be honest about

- The search reads **text only**: notes, layer names, and change kinds. It does not look at the drawing unless AI2 is built, so "when the hair was brown" will only work if a note or layer name says so, or AI2 exists.
- Short or empty notes limit how good the results can be (AI18).
- Embedding models are not perfect. Results are suggestions ranked by similarity, not answers, which is why the animator always checks.
- The first run needs to download the model, so plan how that works on a computer with no internet (AI10).

## Where the code goes

`backend/` holds the search code (text building, index, ranking). The screens are in `gui/`. Nothing in the search code may import or call the commit, restore, merge, or sync code (AI11).
