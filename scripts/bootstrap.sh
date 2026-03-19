#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

log() { echo "[bootstrap] $*"; }

# ── 1. Install Nix ────────────────────────────────────────────────────────────
if ! command -v nix &>/dev/null; then
    log "Installing Nix (Determinate Systems installer)..."
    curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --no-confirm
    # Source nix into current shell
    if [ -e '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' ]; then
        # shellcheck disable=SC1091
        . '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
    fi
else
    log "Nix already installed ($(nix --version))"
fi

# ── 2. Enable experimental features ──────────────────────────────────────────
NIX_CONF="/etc/nix/nix.conf"
if ! grep -q "nix-command" "$NIX_CONF" 2>/dev/null; then
    log "Enabling nix-command and flakes..."
    echo "experimental-features = nix-command flakes" | sudo tee -a "$NIX_CONF" >/dev/null
else
    log "Experimental features already enabled"
fi

# ── 3. Build and test inside the Nix dev shell ───────────────────────────────
log "Configuring CMake..."
nix develop --command cmake -B build -DCMAKE_BUILD_TYPE=Debug

log "Building..."
nix develop --command cmake --build build --parallel

log "Running tests..."
nix develop --command ctest --test-dir build --output-on-failure

log "Bootstrap complete. Enter the dev shell with: nix develop"
