# TraitPeek

A quality-of-life mod for [Whiskerwood](https://store.steampowered.com/app/2489330/Whiskerwood/).

![Trait tags under the worker portraits of a Stone Cutter](docs/screenshot.png)

Whiskers' traits (Swift, Unsafe worker, Gifted Teacher…) decide who is good at which job, but the building window only shows portraits. TraitPeek puts each worker's traits as small tags right under their portrait, so you don't have to open the whisker list.

## Features

- **Tags under each portrait**, matched to the right whisker by name, in every building with worker slots (production, harvesting, farms, services…).
- **Colour-coded**: green = good trait, red = bad trait, beige = neutral.
- **Trait names in the game's language**, taken from the game's own text (`trait.<id>` keys).
- **Stays out of the way**: hidden while the whisker picker is open, gone when the building window closes, doesn't block clicks.
- Updates five times a second, also while paused.

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
| `sync-from-modkit.sh` | Copies the mod's assets from the modkit into this repo; `--release` also stages the built `.pak` for upload. |
| `sync-from-modkit.bat` | Windows version: copies the assets and stages the built `.pak` + uplugin into `workshop/content/`. |
| `sync-to-steam.bat` | Uploads `workshop/content/` to the Workshop with SteamCMD. |

## Building from source

1. Set up the official [Whiskerwood modkit](https://github.com/Whiskerwood-Modding/Whiskerwood-Project) (custom UE 5.6 build, see its README).
2. Copy `Mod/TraitPeek/` from this repo to `Content/Mods/TraitPeek/` in the modkit project.
3. Open the project, right-click the `TraitPeek` folder → **Cook & Install** (Mod Tools).
4. After editing in the editor, run `./sync-from-modkit.sh` (Git Bash) to copy the changed assets back into `Mod/TraitPeek/`, then commit.
   The script assumes the modkit is at `E:\modding\Whiskerwood-Project`; override with `MODKIT=/e/other/path ./sync-from-modkit.sh`.

### Regenerating a graph

`python tools/traitpeek_build.py` writes fresh paste text into `tools/out/` (needs the modkit's `Content/DynamicClasses/Whiskerwood-*.jmap.gz`; set `JMAP=...` if it isn't next to this repo). In the asset's graph: Ctrl+A, Delete, Ctrl+V, compile. Hand edits that the generator doesn't reproduce:

- `WBP_TraitChip` designer: `ChipBorder` brush colour `#242528` (the game's trait-tag grey), padding 6/2.
- If a **Cast To …** node's blue output pin pastes unconnected, drag it to the node it feeds (Get Text / m_isAgentSelectOpen).

## How it works

| Asset | Role |
|---|---|
| `BP_MapLoad` | Runs when a save loads; creates `WBP_TraitPeek` and adds it to the viewport. |
| `WBP_TraitPeek` | Full-screen, click-through overlay. Every 0.2 s (real time) it finds the open building window (any `ArcoView` whose `Context` is a `GridActor`), collects the whiskers whose `Prototype_Agent.GetWorkplace()` is that building, and (re)builds one `WBP_TraitColumn` per worker when the set changes. It then searches the window with the game's `NaviUi.FindDecendentsOfClasses` for the portraits' name labels (`TextBlock`s named `string_name` inside `WorkerSlot_CircleDesign`), matches each label's text to a worker's `agentName`, and places that worker's column 88 units below the label. While the panel's `WorkerAssignmentPanel.m_isAgentSelectOpen` is set (the whisker picker is open), all columns are hidden. |
| `WBP_TraitColumn` | One worker's tags: reads `m_characteristics.traits`, looks up the display name via `LocManager.GetWordFromKey("trait.<id>")`, picks the colour from a fixed good/bad list, and adds a `WBP_TraitChip` per trait to a wrap box. |
| `WBP_TraitChip` | A single tag: grey border + text, text tinted with the trait's colour. |
| `PAL_TraitPeek` | Primary Asset Label that puts the mod into its own pak chunk. |

The game's trait table (`ArcoGameInstance.m_whiskerTraits`) isn't reachable from mods, so good/bad is a hard-coded list of the 30 trait ids that exist in 0.7.207. A trait added in a later game version shows with the neutral colour, and with its raw id if it has no `trait.<id>` text.

## Known limitations

- The vertical offset (88 units under the name label) was tuned by eye; if a game update changes the portrait card layout, the tags may overlap the stats row.
- Two workers with exactly the same name in one building would both get the first one's tags.
- `WBP_TraitPeek` still writes a debug line to `modlog.txt` each time the set of portraits in an open window changes.

## Credits

Created using the Whiskerwood modkit: https://github.com/Whiskerwood-Modding/Whiskerwood-Project
