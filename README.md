# GitHub Search MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to search GitHub repositories with specialized support for CVE (Common Vulnerabilities and Exposures) research and proof-of-concept discovery.

## 🎯 Features

- **GitHub Repository Search**: Full integration with GitHub's search API
- **CVE-Focused Research**: Specialized prompts for vulnerability research
- **PoC Discovery**: Find proof-of-concept code and exploit repositories
- **Rich Metadata**: Get detailed repository information including URLs, stars, forks, and more
- **Authentication Support**: Optional GitHub token for higher rate limits
- **Advanced Search Strategies**: Built-in prompts for comprehensive CVE research

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- `uv` (recommended) or `pip`
- Optional: GitHub Personal Access Token for higher API rate limits

### Installation

1. **Clone or download the server file**

```bash
# Create a new directory for your MCP server
mkdir github-search-mcp
cd github-search-mcp

# Save the server code as github_search_server.py
```

2. **Install dependencies**

```bash
# Using uv (recommended)
uv init .
uv add "mcp[cli]" aiohttp

# Or using pip
pip install "mcp[cli]" aiohttp
```

3. **Optional: Set up GitHub authentication**

```bash
# Get a GitHub Personal Access Token from https://github.com/settings/tokens
export GITHUB_TOKEN="your_github_token_here"
```

### Running the Server

**Development mode (with MCP Inspector):**

```bash
uv run mcp dev github_search_server.py
```

**Direct execution:**

```bash
python github_search_server.py
```

## 🔧 Configuration

### Claude Desktop Integration

Add the server to your Claude Desktop configuration:

**macOS/Linux:**

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**

```bash
code %APPDATA%\Claude\claude_desktop_config.json
```

**Configuration:**

```json
{
  "mcpServers": {
    "github-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/github-search-mcp",
        "run",
        "github_search_server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### Environment Variables

| Variable       | Description                                     | Required             |
| -------------- | ----------------------------------------------- | -------------------- |
| `GITHUB_TOKEN` | GitHub Personal Access Token for authentication | No (but recommended) |

## 📚 API Reference

### Tools

#### `search_github_repositories`

Search GitHub repositories using the GitHub API.

**Parameters:**

- `query` (string, required): Search query with keywords and qualifiers
- `sort` (string, optional): Sort by "stars", "forks", "help-wanted-issues", "updated", or "best-match" (default)
- `order` (string, optional): "desc" (default) or "asc"
- `per_page` (integer, optional): Results per page, 1-100 (default: 30)
- `page` (integer, optional): Page number (default: 1)

**Example Usage:**

```python
# Basic CVE search
search_github_repositories("CVE-2023-1234")

# Advanced search with filters
search_github_repositories(
    "CVE-2023-1234 poc OR exploit language:python",
    sort="updated",
    order="desc",
    per_page=50
)
```

**Returns:**

```json
{
  "search_query": "CVE-2023-1234",
  "total_count": 42,
  "incomplete_results": false,
  "page": 1,
  "per_page": 30,
  "repositories": [
    {
      "name": "cve-2023-1234-poc",
      "full_name": "security-researcher/cve-2023-1234-poc",
      "description": "Proof of concept for CVE-2023-1234",
      "html_url": "https://github.com/security-researcher/cve-2023-1234-poc",
      "clone_url": "https://github.com/security-researcher/cve-2023-1234-poc.git",
      "owner": {
        "login": "security-researcher",
        "html_url": "https://github.com/security-researcher"
      },
      "language": "Python",
      "stars": 15,
      "forks": 3,
      "created_at": "2023-06-15T10:30:00Z",
      "updated_at": "2023-08-20T14:22:00Z",
      "private": false,
      "archived": false,
      "license": "MIT License"
    }
  ]
}
```

### Prompts

#### `cve_repository_search`

Generate targeted search strategies for specific CVE numbers.

**Parameters:**

- `cve_number` (string, required): CVE identifier (e.g., "CVE-2023-1234")
- `include_poc` (boolean, optional): Include PoC-specific terms (default: true)

#### `advanced_cve_search_strategies`

Comprehensive guide for advanced CVE repository searching techniques.

## 🔍 Search Examples

### Basic CVE Search

```bash
# Search for a specific CVE
search_github_repositories("CVE-2023-1234")
```

### Advanced CVE Searches

```bash
# PoC-focused search
search_github_repositories("CVE-2023-1234 poc OR exploit OR vulnerability")

# Language-specific search
search_github_repositories("CVE-2023-1234 language:python")

# Recent activity focus
search_github_repositories("CVE-2023-1234 pushed:>2023-01-01")

# Quality-filtered search
search_github_repositories("CVE-2023-1234 stars:>5 forks:>2")
```

### GitHub Search Qualifiers

The server supports all GitHub search qualifiers:

| Qualifier   | Example                      | Description                            |
| ----------- | ---------------------------- | -------------------------------------- |
| `language:` | `language:python`            | Search by programming language         |
| `stars:`    | `stars:>10`                  | Filter by star count                   |
| `forks:`    | `forks:>5`                   | Filter by fork count                   |
| `created:`  | `created:>2023-01-01`        | Filter by creation date                |
| `pushed:`   | `pushed:>2023-06-01`         | Filter by last push date               |
| `user:`     | `user:microsoft`             | Search in specific user's repositories |
| `org:`      | `org:github`                 | Search in specific organization        |
| `in:`       | `in:name,description,readme` | Search in specific fields              |

## 🛡️ Security Considerations

### Rate Limiting

- **Without token**: 60 requests/hour per IP
- **With token**: 5,000 requests/hour per token
- The server includes error handling for rate limit exceeded scenarios

### PoC Code Safety

When using this server to find vulnerability PoCs:

✅ **Best Practices:**

- Verify repository authenticity and author credibility
- Review code before execution
- Use in isolated/sandboxed environments
- Respect responsible disclosure practices
- Check for proper attribution and references

⚠️ **Warning Signs:**

- Anonymous or suspicious authors
- Lack of documentation
- Obfuscated or unclear code
- No proper attribution
- Encouragement of malicious use

## 🐛 Troubleshooting

### Common Issues

**"GitHub API service unavailable" error:**

- Check GitHub status at https://www.githubstatus.com/
- Retry after a few minutes

**"Invalid search query" error:**

- Verify search syntax using GitHub's search documentation
- Ensure special characters are properly formatted

**Rate limit exceeded:**

- Add a GitHub token to increase rate limits
- Reduce request frequency
- Use more specific search queries

**No results found:**

- Try broader search terms
- Check CVE number formatting
- Use alternative CVE formats (CVE-2023-1234 vs CVE20231234)

### Debug Mode

Run with debug logging:

```bash
python github_search_server.py --debug
```

## 📖 GitHub Search Documentation

For more information about GitHub search syntax and qualifiers:

- [GitHub Search Documentation](https://docs.github.com/en/search-github)
- [GitHub API Search Repositories](https://docs.github.com/en/rest/search#search-repositories)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop](https://claude.ai/download)

## 📞 Support

For issues and questions:

- Check the troubleshooting section above
- Review GitHub API documentation
- Check MCP documentation for client integration issues

---

**Disclaimer**: This tool is for legitimate security research and educational purposes. Users are responsible for ensuring their use complies with applicable laws and GitHub's terms of service.
