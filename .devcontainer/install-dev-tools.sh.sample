#!/bin/bash
# Template: Copy this file to '.devcontainer/install-dev-tools.sh' to customize your local workspace.
# This script runs automatically on your local machine, but is ignored on CI.

# Exit immediately if any command fails, or if an unassigned variable is used.
set -euo pipefail

echo "========================================="
echo "⚙️ Running local environment setup..."
echo "========================================="

# 1. Resolve and set the accurate NVM path dynamically
if [ -d "/usr/local/share/nvm" ]; then
    # Default path inside official MS Dev Container base images
    export NVM_DIR="/usr/local/share/nvm"
    echo "📦 System-level NVM installation detected at: $NVM_DIR"
elif [ -d "$HOME/.nvm" ]; then
    # Standard user-level fallback path
    export NVM_DIR="$HOME/.nvm"
    echo "📦 User-level NVM installation detected at: $NVM_DIR"
else
    # Fresh setup fallback if NVM is missing entirely
    export NVM_DIR="$HOME/.nvm"
    echo "📦 NVM not found. Downloading fresh user-level instance..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi

# Load NVM cleanly into this active shell process sequence
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
else
    echo "❌ Error: nvm.sh could not be found or loaded." >&2
    exit 1
fi

# 2. Install Node.js (Claude Code requires Node 18 or higher)
echo "🟢 Ensuring Node.js (LTS v22) is installed..."
nvm install 22
nvm use 22
nvm alias default 22

# 3. Check and install Anthropic Claude Code CLI
if command -v claude &> /dev/null; then
    echo "✨ Claude Code is already installed."
else
    echo "🤖 Installing Anthropic Claude Code CLI..."
    # Global npm install without sudo to avoid permission conflicts
    npm install -g @anthropic-ai/claude-code@latest
fi

echo "========================================="
echo "🔍 Running Automated Verification Tests..."
echo "========================================="

# Test Node.js binary presence and version parsing
if command -v node &> /dev/null; then
    echo "✅ Node.js verification passed: $(node -v)"
else
    echo "❌ Error: Node.js binary could not be resolved on PATH." >&2
    exit 1
fi

# Test npm package manager binary presence and version parsing
if command -v npm &> /dev/null; then
    echo "✅ npm verification passed: v$(npm -v)"
else
    echo "❌ Error: npm binary could not be resolved on PATH." >&2
    exit 1
fi

# Test Claude Code CLI compilation execution status
# Note: We query the version flag string to verify execution layout
if command -v claude &> /dev/null; then
    echo "✅ Claude Code verification passed: $(claude --version)"
else
    echo "❌ Error: Claude Code binary could not be resolved on PATH." >&2
    exit 1
fi

echo "========================================="
echo "🎉 Local workspace verification complete!"
echo "========================================="

