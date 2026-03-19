#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

log() { echo "[bootstrap] $*"; }

# ── 1. Nix path ───────────────────────────────────────────────────────────────
# Source Nix if it's installed but not yet on PATH
if [ -e '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' ]; then
    # shellcheck disable=SC1091
    . '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
fi

if command -v nix &>/dev/null; then
    # ── Nix path ──────────────────────────────────────────────────────────────
    log "Nix found ($(nix --version)) — using flake dev shell"

    NIX_CONF="/etc/nix/nix.conf"
    if ! grep -q "nix-command" "$NIX_CONF" 2>/dev/null; then
        log "Enabling nix-command and flakes..."
        echo "experimental-features = nix-command flakes" | sudo tee -a "$NIX_CONF" >/dev/null
    fi

    log "Configuring CMake..."
    nix develop --command cmake -B build -DCMAKE_BUILD_TYPE=Debug

    log "Building..."
    nix develop --command cmake --build build --parallel

    log "Running tests..."
    nix develop --command ctest --test-dir build --output-on-failure

    log "Enter the dev shell with: nix develop"

else
    # ── Fallback: system tools (cloud/CI environments without Nix) ────────────
    log "Nix not available — falling back to system package manager"

    if command -v apt-get &>/dev/null; then
        log "Installing build deps via apt..."
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends \
            cmake \
            ninja-build \
            g++ \
            clang \
            python3 \
            python3-pip \
            git \
            curl \
            ca-certificates
    elif command -v brew &>/dev/null; then
        log "Installing build deps via brew..."
        brew install cmake ninja llvm python3
    else
        log "WARNING: No supported package manager found (apt/brew). Assuming deps are pre-installed."
    fi

    log "Configuring CMake..."
    cmake -B build -DCMAKE_BUILD_TYPE=Debug -G Ninja

    log "Building..."
    cmake --build build --parallel

    log "Running tests..."
    ctest --test-dir build --output-on-failure

    log "Bootstrap complete (system tools mode)"
fi
