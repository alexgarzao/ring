# Installing ring for Codex

Quick setup to enable ring skills in Codex.

## Installation

1. **Clone ring repository**:
   ```bash
   mkdir -p ~/.codex/ring
   cd ~/.codex/ring
   git clone https://github.com/lerianstudio/ring.git .
   ```

2. **Create personal skills directory**:
   ```bash
   mkdir -p ~/.codex/skills
   ```

3. **Update ~/.codex/AGENTS.md** to include this ring section:
   ```markdown
   ## ring System

   <EXTREMELY_IMPORTANT>
   You have ring. ring teach you new skills and capabilities. RIGHT NOW run: `~/.codex/ring/.codex/ring-codex bootstrap` and follow the instructions it returns.
   </EXTREMELY_IMPORTANT>
   ```

## Verification

Test the installation:
```bash
~/.codex/ring/.codex/ring-codex bootstrap
```

You should see skill listings and bootstrap instructions. The system is now ready for use.