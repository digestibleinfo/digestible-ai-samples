# autoclip on a two-hour recorded game: sample pack

Test data for the video "Free Opus Clip Alternative on a Normal PC: Can It Clip a 2-Hour Game Stream?" (Digestible AI).
I ran the free, MIT-licensed autoclip desktop app (v1.6.0, Windows) on one two-hour recording, twice with the same settings:
run 1 fully local (Ollama qwen2.5vl:7b + Whisper base), run 2 with DeepSeek. Every clip was checked by my own script
(`files/scripts/check_clips.py`), not by the app's scores. Opus Clip was NOT tested; its prices are quoted from its pricing page
(read 2026-11-24) in the video description only.

## Numbers

| | Run 1 local | Run 2 DeepSeek |
|---|---|---|
| Wall time | 18.2 min | 17.9 min |
| Cost | $0 | under 1 cent (19,104 tokens in, 3,190 out, from DeepSeek's price list) |
| Clips | 10 | 10 |
| Plays | 10/10 | 10/10 |
| Vertical 9:16 | 10/10 | 10/10 |
| Clean cuts (not inside a sentence) | 8/10 | 7/10 |
| Captions readable (WER <= 15 %) | 8/8 checked | 8/8 checked |
| Length inside 30-90 s | 2/10 | 0/10 |
| All checks together (strict) | 1/10 | 0/10 |
| All checks ignoring length | 8/10 | 7/10 |
| Peak VRAM | 9.1 GB of 16 GB | not the point (cloud model) |

The app targets 90-180 s clips and the length cannot be set; every clip also ends with a 1.8 s branded outro (clip lengths 86-178 s).
Run 1's vision step timed out and the app fell back to the transcript.
Full per-run data: `files/results/run1`, `files/results/run2` (`run.json`, `check.json`, `caption_check.json`, `clips_meta.json`, `quality_report.json`, `gpu.csv`, `llm_usage.jsonl`, contact sheet), and `files/results/summary.json`.

## The honest weak result

The footage is ours and it is hard for this kind of tool: a bot match in which the camera never moves, and only 4.7 % of the
two hours is speech (our own synthetic commentary, 80 sentences). Part of the weak result is the footage, not only the app.
It is a recording, not a live stream, and not another game. One run each, no retries. The app is built for streams
(OBS integration), which we did not test.

## The source video

Too big for git (1.13 GB, 116.7 min), so it is not included. Instead:
- `files/source/source.sha256`: SHA-256 of the file we used.
- `files/source/truth.json`: the commentary sentences with their exact times in the source (the ground truth for the cut checks).
- `files/source/narration.txt`: the commentary script. Voice: Qwen3-TTS, mixed over the game video by `files/scripts/mix_source.py`.
- How the game was made: 0 A.D. 0.28.0, observer match, 6 Petra bots, random Mainland map (256 tiles), seed 8 on the take used, victory condition "endless", game sound off. Recorded with ffmpeg gdigrab at about 30 fps by `files/scripts/supervise.ps1` (it restarts the match if the game window closes; the first three takes closed by themselves). `files/scripts/cam.ps1` was meant to move the camera by minimap clicks but did not visibly move it, so the camera is static.
- `files/source/settings.txt`: the frozen app settings used in both runs (telemetry off, same prompts and options).

## Rerun it

1. Install autoclip 1.6.0 (Windows) and, for run 1, Ollama with `qwen2.5vl:7b` (context 16384) and the in-app Whisper base.
2. Make your own recording (or any long one), load it in the app, click Generate, wait about 18 minutes.
3. Copy the output clips to a folder and run `files/scripts/check_clips.py` (needs ffmpeg and ffprobe on PATH; edit the paths at the top; the scripts use `WORKDIR` as a placeholder for a working folder) with a truth file like `truth.json`.
4. Compare with `files/results/*/check.json`.

## Excerpts

`files/excerpts/` holds one 20 s, 480p excerpt per run of an output clip (re-encoded small; the full clips are 28-80 MB each).
The contact sheets show stills from all clips. Everything with game frames is derived from 0 A.D.

## Attribution

0 A.D. by Wildfire Games (https://play0ad.com, http://www.wildfiregames.com/). Its art and audio are licensed CC BY-SA 3.0
(https://creativecommons.org/licenses/by-sa/3.0/), its code GPL-2.0; the licence texts we read are in `files/source/0ad_art_LICENSE.txt`
and `0ad_audio_LICENSE.txt`. Any 0 A.D. frames, clips and contact sheets in this pack are therefore CC BY-SA 3.0 as well; the
commentary, scripts and result data are ours (scripts MIT, see the top README). autoclip is by its authors under the MIT licence.

## Caveats

Windows 11, RTX 5060 Ti 16 GB, 64 GB RAM. Whisper adds a 406 MB download; the app stored about 3.9 GB on the system drive after two runs
(removed by the uninstaller's delete-data box). Telemetry is on by default; we turned it off. The installer is unsigned.
