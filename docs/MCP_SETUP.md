# MCP Server Setup Guide

## Overview
Model Context Protocol (MCP) servers enhance GitHub Copilot with additional tools and context.

## Configuration File
MCP servers are configured in `.github/copilot-mcp.json`

## Environment Variables Required

Create a `.env` file in your project root with:

```bash
# GitHub MCP Server
GITHUB_TOKEN=ghp_your_github_personal_access_token_here

# Figma MCP Server
FIGMA_TOKEN=your_figma_personal_access_token_here

# Supabase MCP Server (if using)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# PostgreSQL (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## Setup Steps

### 1. GitHub MCP Server
```bash
# No additional setup needed - uses your GitHub CLI token
gh auth status
```

### 2. Figma MCP Server
1. Go to Figma → Settings → Personal Access Tokens
2. Create new token with read access
3. Add to `.env` as `FIGMA_TOKEN`

### 3. Python SDK MCP Server
```bash
# Install the Python MCP server package
pip install mcp-server-python-sdk
```

### 4. Supabase MCP Server
1. Go to your Supabase project settings
2. Copy Project URL and Service Role Key
3. Add to `.env`

### 5. Filesystem MCP Server
```bash
# No setup needed - automatically installed via npx
```

## Verify Setup

After configuration, restart VS Code and check:
1. GitHub Copilot is active
2. MCP servers appear in Copilot's context menu
3. No error messages in the output panel

## Troubleshooting

### "Command not found" errors
```bash
# Ensure npx is available
npm install -g npx

# Or use Node.js 18+
node --version
```

### Environment variables not loading
- Restart VS Code completely
- Check `.env` file is in project root
- Verify no typos in variable names

### MCP server not appearing
1. Check `.github/copilot-mcp.json` syntax
2. Verify JSON is valid
3. Restart GitHub Copilot extension

## Available MCP Servers

| Server | Purpose | Status |
|--------|---------|--------|
| GitHub | Repository operations, PRs, issues | ✅ Configured |
| Figma | Design file access | ⚙️ Needs token |
| Python SDK | Python documentation | ⚙️ Needs install |
| Supabase | Database operations | ⚙️ Needs credentials |
| Filesystem | Local file operations | ✅ Auto-install |

## Usage Examples

Once configured, Copilot can:
- **GitHub**: "List open issues in this repo"
- **Figma**: "Show components from [figma-file-url]"
- **Python SDK**: "Generate FastAPI endpoint with validation"
- **Supabase**: "Query users table with filters"

## Security Notes

⚠️ **Never commit tokens to Git!**
- Add `.env` to `.gitignore`
- Use environment variables only
- Rotate tokens regularly
- Use minimal required permissions

## Documentation Links

- [MCP Official Docs](https://modelcontextprotocol.io)
- [GitHub Copilot MCP Guide](https://github.com/features/copilot)
- [Available MCP Servers](https://github.com/modelcontextprotocol/servers)
