# Talking Vegetables — Urdu Comedy Shorts

This is a clean replacement for the old Factora history/facts project.

## Characters
- Rocky Potato
- Brock Broccoli
- Caro Carrot
- Tommy Tomato

The four supplied reference images are included as transparent PNG character assets.

## What each run creates
- One original four-scene Pakistani Urdu comedy story.
- Urdu voice narration with Edge TTS.
- A vertical 720x1280 animated video with gentle character bobbing/swaying and a simple speaking-mouth indicator.
- No spoken-dialogue subtitles or scrolling captions.
- A JSON content plan saved beside the MP4.

## Honest animation limitation
This is lightweight 2.5D puppet-style motion from single-pose images. It is not full 3D rigged walking or accurate phoneme-level lip-sync. True walking needs multiple poses or rigged character models.

## GitHub Actions secrets
Add:
- GROQ_API_KEY
- YOUTUBE_CLIENT_ID
- YOUTUBE_CLIENT_SECRET
- YOUTUBE_REFRESH_TOKEN

Workflow schedule: daily at 7:00 PM Pakistan time. You can also run it manually from Actions.
Public upload is configured by default. For a safe test, change YOUTUBE_PRIVACY to private before the first run.

## Before first public run
Run manually once, download the workflow artifact, and watch the MP4. Confirm the generated dialogue, voice, character positioning and output before leaving scheduled public uploads enabled.
