# Migration Guide

This guide helps you transition from a single-platform Ring installation to the multi-platform installer.

## Who Needs This Guide?

- Users with existing Ring installation in `~/.claude/`
- Users switching from manual git clone to the installer
- Users wanting to add Ring to additional platforms (Factory AI, Cursor, Cline)

## Pre-Migration Checklist

1. **Identify current installation:**
   ```bash
   # Check if Ring is installed
   ls -la ~/.claude/plugins/ring/ 2>/dev/null || echo "No Claude Code installation"
   ls -la ~/.factory/ 2>/dev/null || echo "No Factory AI installation"
   ls -la ~/.cursor/.cursorrules 2>/dev/null || echo "No Cursor installation"
   ls -la ~/.cline/prompts/ 2>/dev/null || echo "No Cline installation"
   ```

2. **Check Ring version:**
   ```bash
   cat ~/.claude/plugins/ring/.claude-plugin/marketplace.json 2>/dev/null | grep version
   ```

3. **Backup customizations (if any):**
   ```bash
   # If you've customized any skills or agents
   cp -r ~/.claude/plugins/ring/custom-backup ~/ring-custom-backup
   ```

## Migration Scenarios

### Scenario 1: Git Clone to Installer (Same Platform)

**Current state:** Ring cloned directly to `~/.claude/` or symlinked

**Steps:**
1. Remove the old installation:
   ```bash
   rm -rf ~/.claude/plugins/ring
   ```

2. Clone Ring to a central location:
   ```bash
   git clone https://github.com/lerianstudio/ring.git ~/ring
   ```

3. Run the installer:
   ```bash
   cd ~/ring
   ./installer/install-ring.sh install --platforms claude
   ```

4. Verify installation:
   ```bash
   ./installer/install-ring.sh list
   ```

### Scenario 2: Claude Code to Multi-Platform

**Current state:** Ring only in Claude Code

**Steps:**
1. Keep existing Claude Code installation (or reinstall)
2. Add additional platforms:
   ```bash
   cd ~/ring

   # Add Factory AI
   ./installer/install-ring.sh install --platforms factory

   # Add Cursor
   ./installer/install-ring.sh install --platforms cursor

   # Add Cline
   ./installer/install-ring.sh install --platforms cline
   ```

3. Or install all at once:
   ```bash
   ./installer/install-ring.sh install --platforms auto
   ```

### Scenario 3: Fresh Multi-Platform Install

**Current state:** No Ring installation

**Steps:**
1. Clone Ring:
   ```bash
   git clone https://github.com/lerianstudio/ring.git ~/ring
   cd ~/ring
   ```

2. Run interactive installer:
   ```bash
   ./installer/install-ring.sh
   ```

3. Select platforms from the menu (or choose "auto-detect")

### Scenario 4: Upgrading Existing Multi-Platform

**Current state:** Ring installed via installer to one or more platforms

**Steps:**
1. Check for updates:
   ```bash
   cd ~/ring
   git pull origin main
   ./installer/install-ring.sh check
   ```

2. Update all platforms:
   ```bash
   ./installer/install-ring.sh update
   ```

3. Or sync only changed files:
   ```bash
   ./installer/install-ring.sh sync
   ```

## Post-Migration Verification

### Claude Code
```bash
# Verify files exist
ls ~/.claude/plugins/ring/default/skills/

# Start a new Claude Code session and check for:
# "Ring skills loaded" message at session start
```

### Factory AI
```bash
# Verify droids exist
ls ~/.factory/droids/

# Start Factory AI and verify droid availability
```

### Cursor
```bash
# Verify rules file
cat ~/.cursor/.cursorrules | head -20

# Verify workflows
ls ~/.cursor/workflows/

# Restart Cursor to load rules
```

### Cline
```bash
# Verify prompts
ls ~/.cline/prompts/skills/
ls ~/.cline/prompts/workflows/

# Test by referencing a prompt in Cline
```

## Handling Custom Content

### Preserving Custom Skills

If you've created custom skills:

1. **Before migration:** Copy to backup
   ```bash
   cp -r ~/.claude/plugins/ring/default/skills/my-custom-skill ~/my-custom-skill-backup
   ```

2. **After migration:** Restore
   ```bash
   cp -r ~/my-custom-skill-backup ~/.claude/plugins/ring/default/skills/my-custom-skill
   ```

3. **Re-run installer** to propagate to other platforms:
   ```bash
   ./installer/install-ring.sh sync
   ```

### Custom Hooks

Custom hooks in `~/.claude/plugins/ring/*/hooks/` will be preserved during updates. The installer tracks file hashes and only updates Ring's original files.

### Platform-Specific Customizations

Custom content added to platform directories (e.g., `~/.cursor/workflows/my-workflow.md`) is not managed by Ring and will be preserved.

## Rollback Procedure

If something goes wrong:

### Full Rollback (Remove Ring)
```bash
# Uninstall from all platforms
./installer/install-ring.sh uninstall --platforms claude,factory,cursor,cline

# Or manually remove
rm -rf ~/.claude/plugins/ring
rm -rf ~/.factory/droids ~/.factory/skills ~/.factory/commands ~/.factory/.ring-manifest.json
rm -f ~/.cursor/.cursorrules && rm -rf ~/.cursor/workflows ~/.cursor/.ring-manifest.json
rm -rf ~/.cline/prompts ~/.cline/.ring-manifest.json
```

### Partial Rollback (Specific Platform)
```bash
./installer/install-ring.sh uninstall --platforms cursor
```

### Restore from Git
```bash
# If installer state is corrupted, reinstall from scratch
rm -rf ~/ring
git clone https://github.com/lerianstudio/ring.git ~/ring
cd ~/ring
./installer/install-ring.sh install --platforms auto --force
```

## Troubleshooting Migration Issues

### "Manifest not found" Error
The installer uses `.ring-manifest.json` to track installations. If missing:
```bash
# Force reinstall
./installer/install-ring.sh install --platforms <platform> --force
```

### "Version mismatch" Warning
```bash
# Update local Ring repository
cd ~/ring
git pull origin main

# Then update installations
./installer/install-ring.sh update
```

### Hooks Not Running
After migration, restart Claude Code/Factory AI to reload hooks.

### Cursor Rules Not Loading
1. Verify file exists: `cat ~/.cursor/.cursorrules`
2. Restart Cursor
3. Check Cursor settings for rules enablement

### Permission Denied
```bash
# Fix permissions
chmod +x ~/ring/installer/install-ring.sh
chmod +x ~/ring/installer/install-ring.ps1
```

## FAQ

**Q: Can I keep my manual installation alongside the installer?**
A: Not recommended. The installer tracks state via manifest files. Manual changes may conflict.

**Q: Does migration delete my customizations?**
A: No. The installer only manages Ring's files. Custom content is preserved.

**Q: Can I migrate one platform at a time?**
A: Yes. Install platforms individually: `--platforms claude`, then later `--platforms cursor`, etc.

**Q: What if I use multiple Ring versions?**
A: Not supported. All platforms install from the same Ring source (`~/ring`).

**Q: Can I install Ring to a custom location?**
A: Claude Code plugin path is fixed. For other platforms, custom paths may be supported in future versions.

## Getting Help

- **GitHub Issues:** https://github.com/lerianstudio/ring/issues
- **Installation logs:** Run with `--verbose` flag
- **Dry run:** Test changes with `--dry-run` before applying
