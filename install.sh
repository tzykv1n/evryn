#!/usr/bin/env bash
# ==============================================================================
# EVRYN Installation and Setup Script
#
# Usage:
#   ./install.sh [OPTIONS]
#
# Options:
#   --help, -h          Show this help message
#   --prefix <dir>      Installation prefix directory (default: $HOME/.local)
#   --dev               Install in editable development mode (pip install -e .)
#   --dry-run           Probe environment and display planned actions without making changes
#   --yes, -y           Non-interactive mode (automatically accept confirmations)
#   --uninstall         Uninstall EVRYN binary and local environment hooks
#
# Supported Operating Systems: Linux (x86_64, aarch64)
# Prerequisites: Python >= 3.10, pip, git
# Zero root or sudo privileges required.
# ==============================================================================

set -eu
[ -n "${BASH_VERSION:-}" ] && set -o pipefail 2>/dev/null || true

PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
DEV_MODE=0
DRY_RUN=0
AUTO_YES=0
DO_UNINSTALL=0

# Determine script and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"

# Styling
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    BOLD="\033[1m"
    GREEN="\033[32m"
    YELLOW="\033[33m"
    CYAN="\033[36m"
    RED="\033[31m"
    RESET="\033[0m"
else
    BOLD=""
    GREEN=""
    YELLOW=""
    CYAN=""
    RED=""
    RESET=""
fi

show_help() {
    cat << EOF
${BOLD}EVRYN Unified Scientific Knowledge Discovery Platform — Installer${RESET}

${BOLD}USAGE:${RESET}
  ./install.sh [OPTIONS]

${BOLD}OPTIONS:${RESET}
  --prefix <path>     Target installation prefix (default: \$HOME/.local)
  --dev               Development mode (installs package as editable)
  --dry-run           Inspect environment and print planned operations
  --yes, -y           Automatic confirmation for all prompts
  --uninstall         Safely remove global wrapper and installation hooks
  --help, -h          Display this help message

${BOLD}SYSTEM PREREQUISITES:${RESET}
  • Linux (x86_64 or aarch64)
  • Python 3.10+ (tested up to 3.14)
  • pip and virtual environment tool
  • 4 GB RAM recommended for full dataset benchmarks
EOF
}

# Parse command line flags
while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            PREFIX="$2"
            BIN_DIR="${PREFIX}/bin"
            shift 2
            ;;
        --dev)
            DEV_MODE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --yes|-y)
            AUTO_YES=1
            shift
            ;;
        --uninstall)
            DO_UNINSTALL=1
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${RESET}" >&2
            show_help
            exit 1
            ;;
    esac
done

if [ "${DO_UNINSTALL}" -eq 1 ]; then
    echo -e "${BOLD}${CYAN}=== EVRYN Uninstaller ===${RESET}"
    TARGET_BIN="${BIN_DIR}/evryn"
    if [ "${DRY_RUN}" -eq 1 ]; then
        echo -e "[DRY-RUN] Would remove binary wrapper: ${TARGET_BIN}"
        exit 0
    fi
    if [ -f "${TARGET_BIN}" ] || [ -L "${TARGET_BIN}" ]; then
        rm -f "${TARGET_BIN}"
        echo -e "${GREEN}[✓] Removed binary wrapper: ${TARGET_BIN}${RESET}"
    else
        echo -e "${YELLOW}[!] Binary wrapper not found at ${TARGET_BIN}${RESET}"
    fi
    echo -e "${GREEN}[✓] EVRYN uninstallation completed.${RESET}"
    exit 0
fi

echo -e "${BOLD}${CYAN}======================================================${RESET}"
echo -e "${BOLD}${CYAN}   EVRYN Platform Installation & Environment Setup     ${RESET}"
echo -e "${BOLD}${CYAN}======================================================${RESET}"

# 1. Operating System Check
OS_TYPE="$(uname -s)"
ARCH_TYPE="$(uname -m)"
echo -e "[*] Platform: ${OS_TYPE} (${ARCH_TYPE})"
if [ "${OS_TYPE}" != "Linux" ]; then
    echo -e "${YELLOW}[WARNING] EVRYN is officially targeted for Linux environments.${RESET}"
fi

# 2. Python Detection
PYTHON_BIN=""
for candidate in python3 python python3.14 python3.13 python3.12 python3.11 python3.10; do
    if command -v "${candidate}" >/dev/null 2>&1; then
        PY_VER="$("${candidate}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
        PY_MAJ="$(echo "${PY_VER}" | cut -d. -f1)"
        PY_MIN="$(echo "${PY_VER}" | cut -d. -f2)"
        if [ "${PY_MAJ}" -ge 3 ] && [ "${PY_MIN}" -ge 10 ]; then
            PYTHON_BIN="$(command -v "${candidate}")"
            break
        fi
    fi
done

if [ -z "${PYTHON_BIN}" ]; then
    echo -e "${RED}[ERROR] Python 3.10 or newer is required but could not be located in PATH.${RESET}" >&2
    exit 1
fi
echo -e "${GREEN}[✓] Python Runtime: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))${RESET}"

# 3. Virtual Environment Selection
VENV_DIR="${REPO_ROOT}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
    if [ "${DRY_RUN}" -eq 1 ]; then
        echo -e "[DRY-RUN] Would initialize virtual environment at: ${VENV_DIR}"
    else
        echo -e "[*] Creating isolated virtual environment at: ${VENV_DIR}"
        "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    fi
fi

ENV_PYTHON="${VENV_DIR}/bin/python"
if [ ! -f "${ENV_PYTHON}" ] && [ "${DRY_RUN}" -eq 0 ]; then
    ENV_PYTHON="${PYTHON_BIN}"
fi

# 4. Package Installation Plan
echo -e "[*] Target Prefix: ${PREFIX}"
echo -e "[*] Binary Wrapper: ${BIN_DIR}/evryn"
echo -e "[*] Installation Mode: $([ "${DEV_MODE}" -eq 1 ] && echo "Editable Development (-e)" || echo "Standard User Package")"

if [ "${DRY_RUN}" -eq 1 ]; then
    echo -e "${YELLOW}[DRY-RUN] Inspection completed successfully. No files created or modified.${RESET}"
    exit 0
fi

# 5. Execute pip install
echo -e "[*] Installing EVRYN package dependencies..."
if [ "${DEV_MODE}" -eq 1 ]; then
    "${ENV_PYTHON}" -m pip install -q -e "${REPO_ROOT}"
else
    "${ENV_PYTHON}" -m pip install -q "${REPO_ROOT}"
fi

# 6. Create Binary Wrapper in $BIN_DIR
mkdir -p "${BIN_DIR}"
WRAPPER="${BIN_DIR}/evryn"

cat << EOF > "${WRAPPER}"
#!/usr/bin/env bash
# Autogenerated EVRYN executable wrapper
export PYTHONUNBUFFERED=1
REPO_DIR="${REPO_ROOT}"
ENV_PY="${ENV_PYTHON}"

if [ ! -f "\${ENV_PY}" ]; then
    ENV_PY="\$(command -v python3)"
fi

exec "\${ENV_PY}" -m evryn.cli "\$@"
EOF

chmod +x "${WRAPPER}"
echo -e "${GREEN}[✓] Installed global executable: ${WRAPPER}${RESET}"

# 7. Verification via Doctor
echo -e "\n[*] Running EVRYN diagnostics check..."
if "${WRAPPER}" doctor; then
    echo -e "${GREEN}[✓] EVRYN platform verification succeeded!${RESET}"
else
    echo -e "${YELLOW}[!] Setup completed, but some diagnostic warnings were encountered.${RESET}"
fi

# 8. Path Advice
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "\n${BOLD}${YELLOW}[NOTE] ${BIN_DIR} is not currently in your system PATH.${RESET}"
    echo -e "To make 'evryn' accessible directly from anywhere, add to your shell profile (~/.bashrc or ~/.zshrc):"
    echo -e "  ${CYAN}export PATH=\"${BIN_DIR}:\$PATH\"${RESET}"
fi

echo -e "\n${BOLD}${GREEN}EVRYN installation complete! Try: evryn --help${RESET}"
