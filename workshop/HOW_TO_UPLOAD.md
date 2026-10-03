# Uploading TraitPeek to the Steam Workshop

Whiskerwood has no in-game uploader; use Valve's [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD).

1. In the modkit (UE 5.8), run **Cook & Install** on `Content/Mods/TraitPeek`.
2. Copy `TraitPeek.pak` from `%localappdata%\Whiskerwood\Saved\mods\TraitPeek\` and
   `Mod/TraitPeek/TraitPeek.uplugin` into `workshop/content/` (git-ignored; the pak is a build artifact).
3. Update `"changenote"` in `TraitPeek.vdf` (and `"Version"` in the uplugin).
4. Run:
   ```
   steamcmd.exe +login YOUR_STEAM_USERNAME +workshop_build_item "E:\modding\whiskerwood-traitpeek\workshop\TraitPeek.vdf" +quit
   ```
5. The first upload writes the new item id into `"publishedfileid"` in the .vdf - commit that change,
   and check the item's visibility on its Workshop page. Later updates: same steps, new changenote.

The preview image is `docs/screenshot.png`.
