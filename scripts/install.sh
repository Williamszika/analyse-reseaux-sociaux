#!/bin/bash
# v3.0 — installe/vérifie les dépendances dans le dossier de travail ($ANALYSES_DIR ou ~/Analyses).
# Usage : bash install.sh          (ordinateur Mac ou Linux : tout, y compris Whisper)
#         bash install.sh --leger  (espace cloud : seulement ce qu'il faut pour timing/report/calendrier/coherence)
set -e
BASE="${ANALYSES_DIR:-$HOME/Analyses}"
mkdir -p "$BASE/cache" "$BASE/rapports"
cd "$BASE"
if [ "$1" = "--leger" ]; then
  pip install -q --break-system-packages weasyprint jinja2 matplotlib pillow numpy pymupdf 2>/dev/null \
    || pip install -q weasyprint jinja2 matplotlib pillow numpy pymupdf
  python3 -c "import weasyprint, jinja2, matplotlib; print('OK (léger)')"
  exit 0
fi
MISSING=""
if [ "$(uname)" = "Darwin" ]; then
  if command -v brew >/dev/null 2>&1; then
    for p in ffmpeg pango; do
      brew list "$p" >/dev/null 2>&1 || brew install "$p" || MISSING="$MISSING brew install $p;"
    done
  else
    MISSING="$MISSING Homebrew (https://brew.sh) puis brew install ffmpeg pango;"
  fi
else
  command -v ffmpeg >/dev/null 2>&1 || MISSING="$MISSING sudo apt install ffmpeg libpango-1.0-0 libpangoft2-1.0-0 (ou l'équivalent de votre système);"
fi
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -U pip yt-dlp
pip install -q weasyprint jinja2 matplotlib pillow numpy imageio-ffmpeg pymupdf
if [ "$(uname -m)" = "arm64" ]; then pip install -q mlx-whisper; else pip install -q faster-whisper; fi
command -v ffmpeg >/dev/null 2>&1 || echo "ffmpeg système absent : repli sur imageio-ffmpeg"
[ -n "$MISSING" ] && echo "A installer à la main dans le Terminal :$MISSING"
python -c "import yt_dlp;print('yt-dlp', yt_dlp.version.__version__)"
echo OK
