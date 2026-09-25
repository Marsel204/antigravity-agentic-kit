#!/usr/bin/env bash
# ==============================================================================
# Antigravity Agentic Engineering Kit — Multi-Device Installer
# ==============================================================================

set -euo pipefail

BOLD="$(tput bold 2>/dev/null || echo '')"
GREEN="$(tput setaf 2 2>/dev/null || echo '')"
BLUE="$(tput setaf 4 2>/dev/null || echo '')"
YELLOW="$(tput setaf 3 2>/dev/null || echo '')"
NC="$(tput sgr0 2>/dev/null || echo '')"

info() { echo -e "${BLUE}${BOLD}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}${BOLD}[SUCCESS]${NC} $*"; }
warn() { echo -e "${YELLOW}${BOLD}[WARN]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${HOME}/.gemini/config"
SKILLS_DIR="${CONFIG_DIR}/skills"
PLUGINS_DIR="${CONFIG_DIR}/plugins"
LOCAL_BIN="${HOME}/.local/bin"

echo -e "\n${BOLD}======================================================${NC}"
echo -e "${BOLD}   Antigravity Agentic Engineering Kit Installer     ${NC}"
echo -e "${BOLD}======================================================${NC}\n"

# 1. Ensure target directories exist
info "Preparing directories in ${CONFIG_DIR}..."
mkdir -p "${SKILLS_DIR}" "${PLUGINS_DIR}" "${LOCAL_BIN}"

# 2. Deploy Plugin Bundle
info "Installing plugin to ${PLUGINS_DIR}/agentic-engineering-kit..."
rm -rf "${PLUGINS_DIR}/agentic-engineering-kit"
cp -r "${SCRIPT_DIR}/plugin" "${PLUGINS_DIR}/agentic-engineering-kit"

# 3. Deploy Global Skills directly for instant slash command resolution
info "Deploying global skills to ${SKILLS_DIR}..."
for skill_dir in "${SCRIPT_DIR}/skills"/*; do
  if [ -d "${skill_dir}" ]; then
    skill_name="$(basename "${skill_dir}")"
    rm -rf "${SKILLS_DIR}/${skill_name}"
    cp -r "${skill_dir}" "${SKILLS_DIR}/${skill_name}"
    echo "  -> Installed /${skill_name}"
  fi
done

# 4. Deploy Global Engineering Rules
info "Configuring global rules at ${CONFIG_DIR}/GEMINI.md..."
if [ -f "${CONFIG_DIR}/GEMINI.md" ]; then
  warn "Existing ${CONFIG_DIR}/GEMINI.md detected. Backing up to GEMINI.md.bak"
  cp "${CONFIG_DIR}/GEMINI.md" "${CONFIG_DIR}/GEMINI.md.bak"
fi
cp "${SCRIPT_DIR}/rules/engineering-standards.md" "${CONFIG_DIR}/GEMINI.md"

# 5. Idempotently configure Knowledge Graph Memory MCP Server
info "Configuring Knowledge-Graph Memory MCP server in ${CONFIG_DIR}/mcp_config.json..."
python3 - << 'PYEOF'
import json, pathlib

cfg_path = pathlib.Path.home() / ".gemini" / "config" / "mcp_config.json"
data = {"mcpServers": {}}

if cfg_path.exists():
    try:
        data = json.loads(cfg_path.read_text())
    except Exception:
        pass

data.setdefault("mcpServers", {})
data["mcpServers"]["memory"] = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"]
}
data["mcpServers"]["context-mode"] = {
    "command": "npx",
    "args": ["-y", "context-mode"]
}

cfg_path.write_text(json.dumps(data, indent=2) + "\n")
print("  -> Registered '@modelcontextprotocol/server-memory' and 'context-mode'")
PYEOF

# 6. Check / Install Worktrunk (wt)
if command -v wt >/dev/null 2>&1; then
  success "worktrunk (wt) is already installed: $(wt --version 2>/dev/null || echo 'ready')"
elif command -v cargo >/dev/null 2>&1; then
  info "cargo detected. Installing worktrunk (wt) for Git worktree agent isolation..."
  cargo install worktrunk || warn "Could not install worktrunk via cargo. You can install it manually later."
  if [ -f "${HOME}/.cargo/bin/wt" ]; then
    ln -sf "${HOME}/.cargo/bin/wt" "${LOCAL_BIN}/wt"
    success "worktrunk installed and symlinked to ${LOCAL_BIN}/wt"
  fi
else
  warn "cargo is not installed. To use parallel worktrees (wt), install Rust/Cargo on this machine."
fi

# 7. Check Pytest runner
if command -v pytest >/dev/null 2>&1; then
  success "pytest test runner detected: $(pytest --version 2>/dev/null || echo 'ready')"
else
  info "Configuring dedicated Python dev environment for test execution..."
  mkdir -p "${HOME}/.local/venvs"
  if python3 -m venv "${HOME}/.local/venvs/dev" 2>/dev/null; then
    "${HOME}/.local/venvs/dev/bin/pip" install --quiet pytest
    ln -sf "${HOME}/.local/venvs/dev/bin/pytest" "${LOCAL_BIN}/pytest"
    success "pytest installed and symlinked to ${LOCAL_BIN}/pytest"
  else
    warn "Could not create venv. Make sure python3-venv is installed."
  fi
fi

echo -e "\n${GREEN}${BOLD}Installation Complete!${NC}"
echo -e "Available slash commands in Antigravity:"
echo -e "  ${BOLD}/spec${NC}                 — Clarify requirements & edge cases"
echo -e "  ${BOLD}/plan${NC}                 — Milestone planning with exit criteria"
echo -e "  ${BOLD}/test${NC}                 — Test-driven development scaffold"
echo -e "  ${BOLD}/build${NC}                — Scoped implementation"
echo -e "  ${BOLD}/review${NC}               — Security and concurrency self-audit"
echo -e "  ${BOLD}/ship${NC}                 — Pre-flight test verification, commit, push & PR"
echo -e "  ${BOLD}/pr${NC}                   — Automated GitHub Pull Request creation"
echo -e "  ${BOLD}/engineering-lifecycle${NC}— End-to-end disciplined SDLC workflow"
echo -e "  ${BOLD}/terse-action${NC}         — Token-efficient, action-first output"
echo -e "  ${BOLD}/archify${NC}              — Interactive system & dataflow architecture diagrams"
echo -e "  ${BOLD}/flowchart${NC}            — Clean process, logic, and decision flowcharts"
echo -e "  ${BOLD}/context-mode${NC}         — Sandbox tool outputs to prevent context rot (98% savings)"
echo -e "  ${BOLD}Memory MCP${NC}            — Persistent Knowledge Graph active\n"
