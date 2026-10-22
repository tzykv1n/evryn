#!/usr/bin/env bash
# ==============================================================================
# EVRYN Uninstaller Script
#
# Usage:
#   ./uninstall.sh [OPTIONS]
#
# Options:
#   --prefix <dir>      Installation prefix directory (default: $HOME/.local)
#   --dry-run           Inspect and display planned removals without executing
#   --yes, -y           Automatic confirmation
#   --help, -h          Display this help message
# ==============================================================================

set -eu
[ -n "${BASH_VERSION:-}" ] && set -o pipefail 2>/dev/null || true

PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
DRY_RUN=0
AUTO_YES=0

show_help() {
    cat << EOF
EVRYN Uninstaller

USAGE:
  ./uninstall.sh [OPTIONS]

OPTIONS:
  --prefix <path>     Target installation prefix where evryn was installed (default: \$HOME/.local)
  --dry-run           Display planned operations without removing files
  --yes, -y           Non-interactive mode (automatically confirm deletion)
  --help, -h          Display this help message
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            PREFIX="$2"
            BIN_DIR="${PREFIX}/bin"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --yes|-y)
            AUTO_YES=1
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$1'" >&2
            show_help
            exit 1
            ;;
    esac
done

TARGET_BIN="${BIN_DIR}/evryn"

if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[DRY-RUN] Target binary to remove: ${TARGET_BIN}"
    exit 0
fi

if [ "${AUTO_YES}" -eq 0 ]; then
    read -r -p "Are you sure you want to uninstall EVRYN binary at ${TARGET_BIN}? [y/N] " response
    case "${response}" in
        [yY][eE][sS]|[yY])
            ;;
        *)
            echo "Uninstallation cancelled."
            exit 0
            ;;
    esac
fi

if [ -f "${TARGET_BIN}" ] || [ -L "${TARGET_BIN}" ]; then
    rm -f "${TARGET_BIN}"
    echo "[✓] Successfully removed ${TARGET_BIN}"
else
    echo "[!] File ${TARGET_BIN} not found."
fi

echo "[✓] EVRYN uninstallation complete."
