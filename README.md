# TraitPeek

A quality-of-life mod for [Whiskerwood](https://store.steampowered.com/app/2489330/Whiskerwood/).

![Trait tags under the worker portraits of a Stone Cutter](docs/screenshot.png)

Whiskers' traits (Swift, Unsafe worker, Gifted Teacher…) decide who is good at which job, but the building window only shows portraits. TraitPeek puts each worker's traits as small tags right under their portrait, so you don't have to open the whisker list.

## Features

- **Tags under each portrait**, matched to the right whisker (also when two workers share a name), in every building with worker slots (production, harvesting, farms, services…).
- **Colour-coded**: green = good trait, red = bad trait, beige = neutral.
- **Trait names in the game's language**, taken from the game's own text (`trait.<id>` keys); the two traits whose id differs from their text key (`pessimest`, `unsafeworker`) are mapped to `trait.pessimist` / `trait.unsafe`.
- **Stays out of the way**: hidden while the whisker picker is open, gone when the building window closes, doesn't block clicks.
- **Instant and event-driven**: updates right when you open a building window or click something in it, also while paused; nothing runs while you're not interacting.

## Installing

- **Manually:** put `TraitPeek.pak` and `TraitPeek.uplugin` in
  `%localappdata%\Whiskerwood\Saved\mods\TraitPeek\` (create the folder; file names must stay `TraitPeek.*`).

## Repository layout

| Path | What |
|---|---|
| `Mod/TraitPeek/` | The mod's source assets (`.uasset`) and `TraitPeek.uplugin`. This is the whole mod. |
| `docs/graphs/` | Blueprint graphs as copy-paste text (T3D). Reference only: the `.uasset` files are the source of truth and contain small hand edits (see below). |
| `tools/` | `t3d.py` + `traitpeek_build.py`: Python generator that writes the graphs in `docs/graphs/` from the modkit's reflection dump. |
| `docs/screenshot.png` | Screenshot, also used as the Workshop preview image. |
| `workshop/` | SteamCMD item file (`TraitPeek.vdf`) and [upload steps](workshop/HOW_TO_UPLOAD.md). |

## Building from source

1. Set up the official [Whiskerwood modkit](https://github.com/Whiskerwood-Modding/Whiskerwood-Project) (custom **UE 5.8** build, see its README). Whiskerwood moved from UE 5.6 to 5.8 in October 2026; a pak cooked with the old 5.6 modkit is built for the old engine, so use the 5.8 modkit.
2. Copy `Mod/TraitPeek/` from this repo to `Content/Mods/TraitPeek/` in the modkit project.
3. Open the project, right-click the `TraitPeek` folder → **Cook & Install** (Mod Tools).
4. After editing in the editor, copy the changed `.uasset` files from the modkit back into `Mod/TraitPeek/`, then commit.

### Regenerating a graph

`python tools/traitpeek_build.py` writes fresh paste text into `tools/out/` (needs the modkit's `Content/DynamicClasses/Whiskerwood-*.jmap.gz`; set `JMAP=...` if it isn't next to this repo). In the asset's graph: Ctrl+A, Delete, Ctrl+V, compile. Hand edits that the generator doesn't reproduce:

- `WBP_TraitChip` designer: `ChipBorder` brush colour `#242528` (the game's trait-tag grey), padding 6/2.
- `WBP_TraitLayer` designer: a single **Canvas Panel** named `Root` (**Is Variable** on), Visibility **Not Hit-Testable (Self Only)**. No graph.
- If a **Cast To …** node's blue output pin pastes unconnected, drag it to the node it feeds (Get Text / m_isAgentSelectOpen / m_workers).

Variables (exact names and types):

| Blueprint | Variable | Type |
|---|---|---|
| `BP_MapLoad` | `Debug` | Boolean |
| | `Peek` | User Widget (object reference) |
| `WBP_TraitPeek` | `Debug`, `Bound` | Boolean |
| | `Waited` | Float |
| | `LayerRoot` | Canvas Panel (object reference) |
| | `Anchor` | Widget (object reference) |
| | `Building` | Actor (object reference) |
| | `Workers` | Prototype Agent (object reference) **array** |
| | `Slots` | Worker Slot (structure) **array** |
| | `Key`, `LastKey`, `Dbg`, `LastDbg`, `Source` | String |
| | `ColNames`, `PassNames` | String **array** |
| | `Columns` | WBP_TraitColumn (object reference) **array** |

## How it works

| Asset | Role |
|---|---|
| `BP_MapLoad` | When a save has loaded (`onLoadingFinished`): reads `debug.txt`, creates `WBP_TraitLayer` (always in the viewport, holds the tag columns) and `WBP_TraitPeek`, hands it the layer's canvas and the Debug flag, and enables input. Any key or mouse button released in the world (`Any Key` input event, not consumed, works while paused) "kicks" `WBP_TraitPeek`. |
| `WBP_TraitLayer` | Full-screen, click-through canvas the columns live on. No logic, never ticks anything. |
| `WBP_TraitPeek` | The worker. A kick adds it to the viewport (or restarts its window if it's already there); while it is in the viewport its Tick refreshes every frame, and 0.4 s after the last kick it removes itself, so nothing runs between interactions. It binds the open window's own buttons (prev/next building, +/-, slots, picker, close) to the same kick, because clicks on game UI don't reach input events. A refresh finds the open building window (a visible `ArcoView` whose `Context` is a `GridActor`), reads the workers in slot order from the building's worker component (`Industry`, `FarmBuilding`, `HarvestingCamp`, … `.m_workers.m_workerSlots[].Agent`; unknown building types fall back to whiskers whose `GetWorkplace()` is the building), and rebuilds one `WBP_TraitColumn` per worker when the list changes. It then finds the portraits' name labels (`TextBlock`s named `string_name`) with `NaviUi.FindDecendentsOfClasses`; each label claims the first unused column whose `agentName` matches, so two whiskers with the same name each get their own tags, and the column goes 88 units under the label. While the whisker picker is open (`WorkerAssignmentPanel.m_isAgentSelectOpen`) the columns are hidden and the refresh keeps running until it closes. |
| `WBP_TraitColumn` | One worker's tags: reads `m_characteristics.traits`, looks up the display name via `LocManager.GetWordFromKey("trait.<id>")`, picks the colour from a fixed good/bad list, and adds a `WBP_TraitChip` per trait to a wrap box. |
| `WBP_TraitChip` | A single tag: grey border + text, text tinted with the trait's colour. |
| `PAL_TraitPeek` | Primary Asset Label that puts the mod into its own pak chunk. |

The game's trait table (`ArcoGameInstance.m_whiskerTraits`) isn't reachable from mods, so good/bad is a hard-coded list of the 30 trait ids that exist in 0.7.207. A trait added in a later game version shows with the neutral colour, and with its raw id if it has no `trait.<id>` text.

## Known limitations

- The vertical offset (88 units under the name label) was tuned by eye; if a game update changes the portrait card layout, the tags may overlap the stats row.
- If a worker is assigned or leaves on its own (not through a click) while the window stays open, the tags update on your next click or key press.
- Two workers with the same name are told apart by slot order; the game's portrait order is assumed to match its slot list.

## Debug logging

Published builds log nothing. To see what the mod does, create `%localappdata%\Whiskerwood\Saved\mods\TraitPeek\debug.txt` with any text in it (an empty file counts as off) and load a save: `modlog.txt` then gets a "ready" line and one line per building window whenever the matched names change (`TraitPeek: <building> via <worker component>: <label>=<column> …`).

## Version history

- **1.0** — Fixed missing tags when two workers in a building have the same name. Pessimist and Unsafe worker now show their proper names and red colour (they showed as `pessimest` / `unsafeworker`). Tags now appear and disappear instantly (event-driven instead of checking five times a second). No log output unless `debug.txt` is present.

- **0.2** — Rebuilt with the UE 5.8 modkit for Whiskerwood's Unreal Engine 5.8 update. No behaviour changes.
- **0.1** — First release (UE 5.6).

## Credits

Created using the Whiskerwood modkit: https://github.com/Whiskerwood-Modding/Whiskerwood-Project
