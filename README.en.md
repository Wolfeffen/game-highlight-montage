# game-highlight-montage

**English** | [简体中文](./README.md)

Gameplay Highlight Montage Skill — turn a batch of raw gameplay highlight clips into a rhythm-driven montage video, following a professional editing methodology.

> Designed for AI Agents that follow the `SKILL.md` convention (WorkBuddy, Claude Code, and similar). Once loaded, the agent can run the entire pipeline on its own: media inspection → segment selection → BGM alignment → pre-cut → render → self-check → delivery.

## What It Does

- **Data-driven segment selection** — inter-frame difference energy (YDIF) locates the action-dense windows; Laplacian-variance sharpness detection filters out low-quality footage
- **Editing methodology built in** — reveal collage → energy-ramping fast cuts → golden-ratio extreme cutting → full-performance bookends → official outro
- **Per-game profiles** — separate rhythm profiles for FPS (Overwatch / Valorant / CS:GO / Delta Force) and MOBA (Honor of Kings / League of Legends)
- **Platform-length presets** — Weibo 35s / Douyin 45s / Bilibili 90s recipes with a hard golden-ratio constraint
- **BGM energy alignment** — picks the music window so the video's golden-ratio point lands on the BGM's high-energy plateau
- **BGM construction brief & alignment check** — `bgm_brief.py` writes a precise musical brief for ACE/human composers; `bgm_onset.py` checks whether generated music's drum hits land on the video cuts
- **One-command BGM generation** — `bgm_generate.py` calls a hosted ACE-Step endpoint, generates N candidates, slides a window across each track and auto-scores alignment, then exports a ready-to-use `bgm_best.mp3` (~$0.12 for a 45s video, 5 candidates)
- **BGM style guide** — measured evidence that heavy drums + distorted guitar solo beat pure synth-electronic for FPS montages, with acceptance criteria
- **Fully code-driven effects** — zoom punch, purple frame-flash, tilted slice collage, cinematic letterbox + slow push… all reproducible and editable

## Repository Layout

```
game-highlight-montage/
├── SKILL.md                       # Skill entry (triggers, three rules, 7-step workflow)
├── scripts/
│   ├── motion_energy.py           # Frame-difference energy analysis, ranks high-energy windows
│   ├── sharpness_check.py         # Sharpness check, flags low-quality clips
│   ├── bgm_energy.py              # Per-second BGM energy curve, helps pick the music window
│   ├── bgm_brief.py               # BGM construction-brief generator for composers / ACE
│   ├── bgm_onset.py               # Drum-hit detection + alignment check against video cuts
│   ├── bgm_generate.py            # One-command cloud ACE-Step generation: candidates + sliding-window auto-select
│   ├── bgm_section_check.py       # Per-section audio/video structure check (energy, drum density, cut/drum ratio)
│   └── make_impacts.py            # Synthesize hit/impact sounds for surgical reinforcement without regenerating music
└── references/
    ├── methodology.md             # The complete editing methodology (distilled from real projects)
    ├── game-profiles.md           # Per-game highlight characteristics and structure adjustments
    ├── platform-presets.md        # Platform length presets and parameterized formulas
    ├── bgm-style.md                # BGM style guide: heavy drums + guitar solo, measured data & acceptance criteria
    └── ace-step.md                 # ACE/ACE-Step integration reference: four cloud/local routes and cost comparison
```

## Requirements

| Dependency | Purpose | How to get it |
|---|---|---|
| ffmpeg / ffprobe | Media inspection, pre-cutting, frame extraction | Windows portable build: `https://registry.npmmirror.com/-/binary/ffmpeg-static/b6.1.1/ffmpeg-win32-x64.gz` (gunzip and run) |
| Python 3.10+ (with numpy) | Running the analysis scripts | Any distribution |
| Node.js 18+ | Remotion rendering | Official installer |
| Remotion 4.x (all packages on the exact same version) | Video rendering | `npm install remotion@4.0.526 @remotion/cli@4.0.526 react@19 react-dom@19` |

## Quick Start

1. Download this repository (Code → Download ZIP) or clone it
2. Drop the `game-highlight-montage/` folder into your agent's skills directory, e.g. `~/.workbuddy/skills/`
3. Ask the agent: *"Make a gameplay montage — clips are in directory X, target platform is Douyin"*
4. The agent runs the workflow: media inspection → methodology & game profile → BGM selection and alignment → timeline generation and pre-cut → Remotion render → frame-by-frame self-check → delivers master + share versions

## The Three Rules

| Rule | Why |
|---|---|
| **Look at the footage before choosing segments** | Data is only a first pass. Every candidate must be verified by extracting frames — otherwise reveal animations, black frames or blurry shots slip in |
| **Wind-up frames > post-kill frames** | The payoff comes from a clear wind-up and a decisive kill — roughly 60/40. A 50/50 split reads as "messy" |
| **Rebalance total duration before editing the timeline** | Any addition or removal must re-verify the total length and that the BGM alignment still holds |

## Verification Status

Distilled from a complete real-world project: 27 Overwatch Moira "Play of the Game" clips → a 46.7-second montage, refined through four rounds of expert feedback.

- Overwatch profile: **verified in production**
- Valorant / CS:GO: **extrapolated from the same genre** (both share the short-TTK, no-official-wrapper situation)
- MOBA profile: **awaiting real-world validation**

## License

MIT — see [LICENSE](./LICENSE). Free to use, modify and redistribute.
Sample BGM was sourced from ccMixter; please honor each track's CC license when reusing it.
