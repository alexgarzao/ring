#!/bin/bash
set -e

echo "================================================"
echo "Ring Plugin Marketplace Installer"
echo "================================================"
echo ""

MARKETPLACE_SOURCE="lerianstudio/ring"
MARKETPLACE_NAME="ring"

echo "📦 Adding Ring marketplace from GitHub..."
set +e
marketplace_output=$(claude plugin marketplace add "$MARKETPLACE_SOURCE" 2>&1)
marketplace_exit_code=$?
set -e

if echo "$marketplace_output" | grep -q "already installed"; then
    echo "ℹ️  Ring marketplace already installed"
    read -p "Would you like to update it? (Y/n): " update_marketplace || update_marketplace=""
    
    if [[ ! "$update_marketplace" =~ ^[Nn]$ ]]; then
        echo "🔄 Updating Ring marketplace..."
        if claude plugin marketplace update "$MARKETPLACE_NAME"; then
            echo "✅ Ring marketplace updated successfully"
        else
            echo "⚠️  Failed to update marketplace, continuing with existing version..."
        fi
    else
        echo "➡️  Continuing with existing marketplace"
    fi
elif echo "$marketplace_output" | grep -q "Failed"; then
    echo "❌ Failed to add Ring marketplace"
    echo "$marketplace_output"
    exit 1
else
    echo "✅ Ring marketplace added successfully"
fi
echo ""

echo "🔧 Installing/updating ring-default (core plugin - required)..."
if claude plugin install ring-default 2>&1; then
    echo "✅ ring-default ready"
else
    echo "❌ Failed to install ring-default"
    exit 1
fi
echo ""

echo "================================================"
echo "Additional Plugins Available"
echo "================================================"
echo ""
echo "Active plugins:"
echo "  • ring-developers - 5 specialized developer agents (Go backend, DevOps, Frontend, QA, SRE)"
echo "  • ring-product-reporter - Product Reporter specialized agents and skills"
echo ""
echo "Reserved (coming soon):"
echo "  • ring-product-flowker"
echo "  • ring-product-matcher"
echo "  • ring-product-midaz"
echo "  • ring-product-tracer"
echo "  • ring-team-devops"
echo "  • ring-team-ops"
echo "  • ring-team-pmm"
echo "  • ring-team-product"
echo ""

read -p "Would you like to install ring-developers? (y/N): " install_developers || install_developers=""

if [[ "$install_developers" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔧 Installing/updating ring-developers..."
    if claude plugin install ring-developers 2>&1; then
        echo "✅ ring-developers ready"
    else
        echo "⚠️  Failed to install ring-developers (might not be published yet)"
        install_developers="n"
    fi
fi

read -p "Would you like to install ring-product-reporter? (y/N): " install_reporter || install_reporter=""

if [[ "$install_reporter" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔧 Installing/updating ring-product-reporter..."
    if claude plugin install ring-product-reporter 2>&1; then
        echo "✅ ring-product-reporter ready"
    else
        echo "⚠️  Failed to install ring-product-reporter (might not be published yet)"
        install_reporter="n"
    fi
fi

echo ""
echo "================================================"
echo "✨ Setup Complete!"
echo "================================================"
echo ""
echo "Active plugins:"
echo "  ✓ ring-default (34 skills, 7 commands, 6 agents)"
if [[ "$install_developers" =~ ^[Yy]$ ]]; then
    echo "  ✓ ring-developers (5 developer agents)"
else
    echo "  ○ ring-developers (not installed)"
fi
if [[ "$install_reporter" =~ ^[Yy]$ ]]; then
    echo "  ✓ ring-product-reporter (Product Reporter agents & skills)"
else
    echo "  ○ ring-product-reporter (not installed)"
fi
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code or start a new session"
echo "  2. Skills will auto-load via SessionStart hook"
echo "  3. Try: /ring:brainstorm or Skill tool: 'ring:using-ring'"
echo ""
echo "Marketplace commands:"
echo "  claude plugin marketplace list    # View configured marketplaces"
echo "  claude plugin install <name>      # Install more plugins"
echo "  claude plugin enable <name>       # Enable a plugin"
echo "  claude plugin disable <name>      # Disable a plugin"
echo ""
