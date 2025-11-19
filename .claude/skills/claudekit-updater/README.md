# ClaudeKit Updater Skill

Safely update ClaudeKit Engineer projects to the latest version.

## Quick Start

Just ask Claude:
```
Update my ClaudeKit project
```

or

```
Update Lex-Stream to latest ClaudeKit version
```

Claude will automatically:
1. Create a backup
2. Create a test branch
3. Update the framework
4. Verify the update
5. Give you next steps

## What It Does

- ✅ Updates agents, commands, workflows
- ✅ Adds new skills (19 in v1.14.0)
- ✅ Adds new commands (9 new)
- ✅ Preserves your code and settings
- ✅ Creates backups
- ✅ Runs verification checks

## Safety

- Never touches your project code
- Always creates timestamped backups
- Uses test branches (safe mode)
- Easy rollback if needed
- Preserves settings.local.json

## Examples

**Update one project:**
```
Update ~/Lex-Stream
```

**Update all projects:**
```
Update all my ClaudeKit projects
```

**Quick mode (no test branch):**
```
Quickly update ~/my-project
```

**Find projects:**
```
What ClaudeKit projects do I have?
```

## After Update

Test the update:
```bash
cd ~/your-project
claude
/ask "what's new?"
```

Merge if good:
```bash
git checkout main
git merge update-claudekit-YYYYMMDD-HHMMSS
```

## Files

The skill uses these scripts:
- `/Users/sam/claudekit-engineer/update-claudekit-project.sh`
- `/Users/sam/claudekit-engineer/batch-update-example.sh`

Documentation:
- `/Users/sam/claudekit-engineer/UPDATE-PROJECTS.md`
- `/Users/sam/claudekit-engineer/CLAUDE-UPDATE-INSTRUCTIONS.md`

## What's New in v1.14.0

- 19 new skills (ai-multimodal, backend-dev, mobile-dev, databases, etc.)
- 9 new commands (/code, /use-mcp, /review:codebase, etc.)
- Better token efficiency
- Security hooks
- Performance improvements

---

For detailed documentation, see `SKILL.md`
