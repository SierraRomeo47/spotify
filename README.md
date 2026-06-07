# Sierra Romeo Editorial Intelligence Lab

**From DJ Instinct to Editorial Intelligence**

A local Streamlit dashboard that converts personal Spotify listening data into music editorial insights, playlist strategy, artist discovery signals, hip-hop/international affinity analysis, and India/global cultural positioning.

**Portfolio project by Sumit Redu (Sierra Romeo)** — prepared for editorial roles in music and culture. This is **not** an official Spotify product and is not affiliated with Spotify.

---

## 1. Project overview

A **minimal 5-page** employer walkthrough (~2 minutes):

| Page | What to show |
|------|----------------|
| **Home** | Positioning + DJ story |
| **Discovery** | Breakout watchlist + plays per day |
| **Culture & lanes** | India export / global entry tables |
| **Curate** | Playlist sequence proof + top 3 playlist scores |
| **Role Fit** | JD summary with your live artist names (default landing) |

**Production portfolio (Vercel):** Next.js app in `web/` serves pre-built JSON — fast load, no OAuth for recruiters. See [Deploy to Vercel](#deploy-to-vercel-private) below.

**Local Streamlit lab:** Sidebar **Data source** for refresh; auto-loads Exportify + Spotify API on startup (OAuth on first visit).

Honest dual lens: recent listening skews **club/electronic** (e.g. Fred again..); long-term taste includes **India ↔ global hip-hop** (e.g. AP Dhillon, Shubh). All analysis runs **locally**.

---

## 2. Why this project exists

Editorial music roles require taste, cultural context, and data literacy. This dashboard demonstrates how DJ instinct (Sierra Romeo) and professional editorial thinking (Sumit Redu) combine with accessible metadata—without relying on restricted Spotify endpoints like `audio_features` or recommendations.

---

## 3. Role alignment: Spotify Editor, Music & Culture

This project maps directly to:

| Capability | Dashboard feature |
|------------|-------------------|
| Editorial POV | Home, Role Fit |
| Spot trends early | **Discovery** watchlist |
| India ↔ global bridge | **Culture & lanes** |
| Curate with sequencing | **Curate** (builder + playlist scores) |
| Data-led insights | Role Fit + discovery metrics |

### How “discover before famous” works (honest model)

This lab does **not** use Spotify’s internal charts. It models editorial early discovery from **your** listening:

- **Listen velocity** in recently played (plays per artist/track)
- **Not yet in long-term** top artists (exploration before taste lock-in)
- **Low popularity** or **recent releases** when the API provides them
- **First detected date** from `played_at` timestamps
- **YouTube-only** artists as culture-layer leads

Re-fetch via **Connect Spotify** in the sidebar after listening sessions; up to 50 plays per fetch are merged into `recent_history` (200 cap).

---

## 4. Setup

### Prerequisites

- Python 3.11+
- A Spotify account
- (Optional) Spotify Developer app credentials

### Spotify Developer Dashboard

1. Go to [Create an app](https://developer.spotify.com/dashboard/create)
2. App name: **Sierra Romeo Editorial Intelligence Lab**
3. Redirect URI: `http://127.0.0.1:8888/callback`
4. API / SDK: **Web API**
5. Copy **Client ID** and **Client Secret**

### Environment

```bash
cd sierra_romeo_editorial_lab
copy .env.example .env
```

Edit `.env`:

```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
streamlit run streamlit_app.py
```

### Verify Spotify connection

```bash
python scripts/verify_spotify_connection.py
```

### Run tests

```bash
pytest tests/ -v
```

Unit tests use inline fixtures only (not loaded at runtime): `pytest tests/ -v -k "not test_env_credentials and not TestSpotify"`

### Local data (primary)

Place your **Spotify privacy export** under `my_spotify_data/Spotify Account Data/`:

- `StreamingHistory_music_*.json` — extended play history
- `YourLibrary.json` — saved/liked tracks
- `Playlist*.json` — playlist contents

Optional: **Exportify** CSVs in `spotify_playlists/` for genres, popularity, and audio features (merged by track URI).

On startup the app automatically:

1. Loads **my_spotify_data** (streaming, library, playlists).
2. Merges **Exportify** enrichment when CSVs exist.
3. **Fetches Spotify API** data when credentials are set (OAuth on first visit).
4. **Enriches missing genres** via MusicBrainz / Last.fm when configured.

### First use

1. Run `streamlit run streamlit_app.py` — library loads automatically.
2. Complete Spotify login in the browser on first visit (one-time).
3. Open Discovery, Culture, Curate, and Role Fit — data should be populated (`exportify` or `api+exportify`).

---

## 5. Required scopes

- `user-top-read`
- `user-read-recently-played`
- `user-library-read`
- `playlist-read-private`
- `playlist-read-collaborative`

Optional (not used by default): `playlist-modify-private`, `playlist-modify-public`

---

## 6. Known API limitations

Development-mode Spotify apps may not access:

- `audio_features` / `audio_analysis`
- Recommendations, related artists
- Featured / category / Spotify-owned editorial playlists
- Preview URLs

This lab **does not call** those endpoints. It uses top tracks, top artists, recently played, saved tracks, playlists, popularity, genres, release dates, explicit flags, and duration — **API metadata only**.

---

## Deploy to Vercel (private)

The recruiter-facing app is the **Next.js** site in `web/`, not Streamlit.

### 1. Build static data (run locally after data changes)

```bash
cd sierra_romeo_editorial_lab
pip install -r requirements.txt
python scripts/build_site_data.py
```

This writes `web/public/data/portfolio.json` from **my_spotify_data/** plus optional Exportify enrichment and `outputs/` API exports.

### 2. Preview locally

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000 — default landing is **Role Fit** (`/` redirects there).

### 3. Deploy

1. Push to GitHub — Vercel redeploys automatically from `main`.
2. **No dashboard setup required:** root [`vercel.json`](vercel.json) uses `@vercel/static-build` on `web/package.json` (Next.js static export → `web/out`). [`.vercelignore`](.vercelignore) excludes Streamlit and Python files so Vercel never tries a Python entrypoint.
3. Optional: [Vercel](https://vercel.com) → Project Settings → set **Root Directory** to `web` instead if you prefer the Next.js preset (remove root `vercel.json` in that case).
4. Enable **Vercel Authentication** or password protection for recruiter access.
5. No `SPOTIPY_*` env vars needed on Vercel (read-only snapshot).

### 4. Refresh data

1. Update Exportify CSVs and/or refresh Streamlit → `outputs/*.csv`.
2. Re-run `python scripts/build_site_data.py`.
3. Commit `web/public/data/portfolio.json` and redeploy.

---

## 7. YouTube Takeout data (optional)

1. Export from [Google Takeout](https://takeout.google.com/) → YouTube and YouTube Music → watch history (JSON or HTML)
2. On **YouTube / External Culture Signals**, upload the file or a manual CSV with columns:  
   `title`, `channel`, `url`, `watched_at`, `source`, `manual_artist`, `manual_track`, `manual_genre`
3. Treat YouTube as a **culture-signal layer**—matching to Spotify artists is fuzzy, not exact. Upload via session state only when you have a real export.

---

## 8. Assets (DJ photos)

Replace placeholder images in [`assets/`](assets/) with your own (keep filenames):

- `home_hero_background.png` — Home page portfolio banner (main hero)
- `profile_cover.png` — fallback cover (same banner)
- `style_reference.png` — style reference

---

## 9. Privacy

This project analyzes **personal listening data locally**. Do not publish raw listening exports unless intentionally anonymized. Never commit `.env` or `.spotify_cache`.

---

## 10. Portfolio disclaimer

**Sierra Romeo Editorial Intelligence Lab** is an independent portfolio demonstration. It does not use official Spotify branding or imply endorsement by Spotify AB.

---

## Project structure

```
sierra_romeo_editorial_lab/
├── streamlit_app.py       # Local Streamlit lab (data refresh)
├── portfolio_site_builder.py
├── scripts/build_site_data.py
├── web/                   # Next.js → Vercel production
│   ├── app/               # Routes: home, discovery, culture, curate, role-fit
│   ├── public/data/portfolio.json
│   └── next.config.mjs    # output: export → web/out for Vercel
├── vercel.json            # GitHub 1-click deploy from repo root
├── .vercelignore
├── config.py
├── exportify_loader.py
├── spotify_auth.py
├── spotify_fetch.py
├── data_processing.py
├── editorial_engine.py
├── discovery_engine.py
├── listening_tenure.py
├── pages/                 # Streamlit pages (local only)
├── my_spotify_data/       # Spotify privacy export (primary real data)
│   └── Spotify Account Data/
├── spotify_playlists/     # Optional Exportify CSVs (genres/audio enrichment)
└── outputs/
```

---

*Sumit Redu · Sierra Romeo · Mumbai*
