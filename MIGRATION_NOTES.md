# Migration from Make to Just

## What Changed

### Files Created
- ✅ `justfile` - New task runner configuration (replaces Makefile)
- ✅ `INSTALL_JUST.md` - Installation instructions for `just`

### Files Updated
- ✅ `CLAUDE.md` - Updated all references from `make` to `just`

### Files to Keep (for now)
- ⚠️ `Makefile` - Keep as backup until team fully migrates

## Command Migration

| Old (Make) | New (Just) |
|------------|------------|
| `make` | `just` |
| `make install` | `just install` |
| `make dev` | `just dev` |
| `make run` | `just run` |
| `make test` | `just test` |
| `make lint` | `just lint` |
| `make format` | `just format` |
| `make check` | `just check` |
| `make clean` | `just clean` |
| `make branch NAME=feat/x` | `just branch feat/x` |
| `make pr` | `just pr` |

## Key Improvements

1. **Cross-Platform**: Works identically on Windows (PowerShell) and WSL/Linux
2. **Cleaner Syntax**: No need for `.PHONY` declarations or complex escaping
3. **Better Errors**: More helpful error messages
4. **Modern**: Used by projects like uv, ruff, and other modern Python tools

## CI/CD Impact

**No workflow changes needed!** ✅

Your GitHub Actions workflows already use `uv run` commands directly:
- `uv run ruff check soloquest tests`
- `uv run pytest --cov=...`
- `uv run semantic-release version`

The `justfile` is **for local development only** - it provides cross-platform convenience for developers on Windows and WSL/Linux. CI continues to work exactly as before.

## Next Steps

1. **Install `just`** (see INSTALL_JUST.md):
   ```bash
   # Quick install for WSL/Linux:
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

   # Or using cargo:
   cargo install just
   ```

2. **Test the justfile**:
   ```bash
   just             # List all commands
   just test        # Run tests
   just check       # Run lint + tests
   ```

3. **After confirming everything works**:
   ```bash
   # Remove the old Makefile
   git rm Makefile

   # Commit the migration
   git add justfile CLAUDE.md INSTALL_JUST.md MIGRATION_NOTES.md
   git commit -m "chore: migrate from Make to Just for cross-platform local development"
   ```

4. **Team Communication**:
   - Share INSTALL_JUST.md with the team
   - Emphasize: `just` is optional but recommended for local dev
   - CI/CD workflows are unchanged and don't require `just`

## Troubleshooting

### `just: command not found`
- Ensure `just` is installed (see INSTALL_JUST.md)
- Check that the installation directory is in your PATH

### Commands fail with "recipe not found"
- Run `just --list` to see all available commands
- Check for typos in command names

### Different behavior between Windows and WSL
- This should NOT happen with `just` - if it does, please report
- The justfile uses bash for all shell scripts, ensuring consistency

## Rollback Plan

If you need to rollback to Make temporarily:
```bash
# The Makefile still exists, just use it:
make test
make check
```

Once `just` is confirmed working, you can safely remove the Makefile.
