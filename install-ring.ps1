# Ring Plugin Marketplace Installer (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "================================================"
Write-Host "Ring Plugin Marketplace Installer"
Write-Host "================================================"
Write-Host ""

$MARKETPLACE_SOURCE = "lerianstudio/ring"
$MARKETPLACE_NAME = "ring"

Write-Host "📦 Adding Ring marketplace from GitHub..."
try {
    $marketplaceOutput = & claude plugin marketplace add $MARKETPLACE_SOURCE 2>&1 | Out-String
    $marketplaceExitCode = $LASTEXITCODE
} catch {
    $marketplaceOutput = $_.Exception.Message
    $marketplaceExitCode = 1
}

if ($marketplaceOutput -match "already installed") {
    Write-Host "ℹ️  Ring marketplace already installed"
    $updateMarketplace = Read-Host "Would you like to update it? (Y/n)"

    if ($updateMarketplace -notmatch "^[Nn]$") {
        Write-Host "🔄 Updating Ring marketplace..."
        try {
            & claude plugin marketplace update $MARKETPLACE_NAME | Out-Null
            Write-Host "✅ Ring marketplace updated successfully"
        } catch {
            Write-Host "⚠️  Failed to update marketplace, continuing with existing version..."
        }
    } else {
        Write-Host "➡️  Continuing with existing marketplace"
    }
} elseif ($marketplaceOutput -match "Failed") {
    Write-Host "❌ Failed to add Ring marketplace"
    Write-Host $marketplaceOutput
    exit 1
} else {
    Write-Host "✅ Ring marketplace added successfully"
}
Write-Host ""

Write-Host "🔧 Installing/updating ring-default (core plugin - required)..."
try {
    & claude plugin install ring-default 2>&1 | Out-Null
    Write-Host "✅ ring-default ready"
} catch {
    Write-Host "❌ Failed to install ring-default"
    exit 1
}
Write-Host ""

Write-Host "================================================"
Write-Host "Additional Plugins Available"
Write-Host "================================================"
Write-Host ""
Write-Host "Active plugins:"
Write-Host "  • ring-developers - 5 specialized developer agents (Go backend, DevOps, Frontend, QA, SRE)"
Write-Host "  • ring-product-reporter - Product Reporter specialized agents and skills"
Write-Host ""
Write-Host "Reserved (coming soon):"
Write-Host "  • ring-product-flowker"
Write-Host "  • ring-product-matcher"
Write-Host "  • ring-product-midaz"
Write-Host "  • ring-product-tracer"
Write-Host "  • ring-team-devops"
Write-Host "  • ring-team-ops"
Write-Host "  • ring-team-pmm"
Write-Host "  • ring-team-product"
Write-Host ""

$installDevelopers = Read-Host "Would you like to install ring-developers? (y/N)"

if ($installDevelopers -match "^[Yy]$") {
    Write-Host ""
    Write-Host "🔧 Installing/updating ring-developers..."
    try {
        & claude plugin install ring-developers 2>&1 | Out-Null
        Write-Host "✅ ring-developers ready"
    } catch {
        Write-Host "⚠️  Failed to install ring-developers (might not be published yet)"
        $installDevelopers = "n"
    }
}

$installReporter = Read-Host "Would you like to install ring-product-reporter? (y/N)"

if ($installReporter -match "^[Yy]$") {
    Write-Host ""
    Write-Host "🔧 Installing/updating ring-product-reporter..."
    try {
        & claude plugin install ring-product-reporter 2>&1 | Out-Null
        Write-Host "✅ ring-product-reporter ready"
    } catch {
        Write-Host "⚠️  Failed to install ring-product-reporter (might not be published yet)"
        $installReporter = "n"
    }
}

Write-Host ""
Write-Host "================================================"
Write-Host "✨ Setup Complete!"
Write-Host "================================================"
Write-Host ""
Write-Host "Active plugins:"
Write-Host "  ✓ ring-default (34 skills, 7 commands, 6 agents)"
if ($installDevelopers -match "^[Yy]$") {
    Write-Host "  ✓ ring-developers (5 developer agents)"
} else {
    Write-Host "  ○ ring-developers (not installed)"
}
if ($installReporter -match "^[Yy]$") {
    Write-Host "  ✓ ring-product-reporter (Product Reporter agents & skills)"
} else {
    Write-Host "  ○ ring-product-reporter (not installed)"
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Claude Code or start a new session"
Write-Host "  2. Skills will auto-load via SessionStart hook"
Write-Host "  3. Try: /ring:brainstorm or Skill tool: 'ring:using-ring'"
Write-Host ""
Write-Host "Marketplace commands:"
Write-Host "  claude plugin marketplace list    # View configured marketplaces"
Write-Host "  claude plugin install <name>      # Install more plugins"
Write-Host "  claude plugin enable <name>       # Enable a plugin"
Write-Host "  claude plugin disable <name>      # Disable a plugin"
Write-Host ""
