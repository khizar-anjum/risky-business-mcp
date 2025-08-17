# Risky Business AI MCP Server

A comprehensive Model Context Protocol (MCP) server for cybersecurity vulnerability assessment, providing tools to search GitHub repositories, query NIST NVD, access CISA's Known Exploited Vulnerabilities catalog, and analyze repository contents for CVE research and proof-of-concept discovery.

## 📹 Demo

https://github.com/user-attachments/assets/6a3f5a4f-7e0e-4c0f-bdc5-2f5d86ba9b0f

### Demo Workflow

The demo demonstrates a complete vulnerability assessment for CVE-2025-53770:

1. ✅ **Validate CVE-2025-53770 and retrieve severity information from NIST**
2. ✅ **Analyze business impact by checking company asset inventory**
3. ✅ **Check for active exploitation in CISA KEV database**
4. ✅ **Search for proof-of-concept exploits on GitHub**
5. ✅ **Generate executive dashboard with findings**
6. ✅ **Create and deliver voice briefing**
7. ✅ **Send summary to Beeper chat**

### Sample Alert Message (Sent via Beeper)

```
🚨 CRITICAL SECURITY ALERT - CVE-2025-53770 🚨

Severity: CRITICAL (CVSS 9.8)
Status: ⚠️ ACTIVELY EXPLOITED IN THE WILD

Company Impact: 🔴 AFFECTED
• Asset: PROD-SP-01 (SharePoint Server 2019 Enterprise)
• Environment: Production
• Criticality: High

Threat Intelligence:
• Listed in CISA KEV with known ransomware usage
• Multiple proof-of-concept exploits publicly available on GitHub
• Vulnerability allows unauthenticated remote code execution
• This is a patch bypass for CVE-2025-49704

Immediate Actions Required:
✓ Apply Microsoft security updates IMMEDIATELY
✓ If updates cannot be applied, disconnect SharePoint from network
✓ Monitor for suspicious activity in SharePoint logs
✓ Review CISA mitigation guidance

Technical Details:
• CWE-502: Deserialization of Untrusted Data
• Affects SharePoint 2016, 2019, and Subscription Edition
• Exploitation requires network access only (no authentication)

⏰ Due Date: July 21, 2025 (per CISA BOD 22-01)

Voice briefing has been generated. Please take immediate action to protect company assets.
```

## 🛠️ Tools

### `search_github_repositories`
Search GitHub repositories using the GitHub API.

**Parameters:**
- `query` (string, required): Search query with keywords and qualifiers
- `sort` (string, optional): Sort by "stars", "forks", "help-wanted-issues", "updated", or "best-match" (default)
- `order` (string, optional): "desc" (default) or "asc"
- `per_page` (integer, optional): Results per page, 1-100 (default: 5)
- `page` (integer, optional): Page number (default: 1)

### `get_cve_from_nist`
Query NIST National Vulnerability Database for CVE details.

**Parameters:**
- `cve_id` (string, required): CVE identifier (e.g., "CVE-2023-1234" or "2023-1234")

**Returns:** CVSS scores, severity ratings, CWE mappings, affected products (CPE), and references.

### `search_kev`
Search CISA's Known Exploited Vulnerabilities catalog.

**Parameters:**
- `query` (string, required): Search term (CVE ID, vendor, product, or keyword)
- `field` (string, optional): Field to search - "all", "cve_id", "vendor", "product", "vulnerability_name", "date_added" (default: "all")
- `max_results` (integer, optional): Maximum results 1-50 (default: 10)

**Returns:** Matching KEV entries with exploitation details and ransomware campaign indicators.

### `list_github_repository_files`
List all files in a GitHub repository.

**Parameters:**
- `repo_url` (string, required): GitHub repository URL (e.g., "https://github.com/owner/repo")
- `branch` (string, optional): Branch name (default: "main")

**Returns:** Complete file tree with paths, types, and SHA hashes.

### `get_github_file_content`
Retrieve specific file content from a GitHub repository.

**Parameters:**
- `repo_url` (string, required): GitHub repository URL
- `file_path` (string, required): Path to file (e.g., "src/exploit.py")
- `branch` (string, optional): Branch name (default: "main")

**Returns:** File content (text or binary indicator) with metadata.

## 📝 Prompts

### `cve_repository_search`
Generate targeted search strategies for specific CVE numbers.

**Parameters:**
- `cve_number` (string, required): CVE identifier (e.g., "CVE-2023-1234")
- `include_poc` (boolean, optional): Include PoC-specific terms (default: true)

### `advanced_cve_search_strategies`
Comprehensive guide for advanced CVE repository searching techniques.

## 📊 Resources

### `kev://cisa/catalog`
Access the complete CISA Known Exploited Vulnerabilities catalog with active exploitation data.

### `assets://company/inventory`
Company asset inventory for vulnerability impact assessment, including environment, criticality, and vendor information.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- `uv` (recommended) or `pip`
- Optional: GitHub Personal Access Token for higher API rate limits
- Optional: NIST API Key for increased rate limits

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/khizar-anjum/risky-business-mcp.git
cd risky-business-mcp
```

2. **Set up Python virtual environment**

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Optional: Set up API authentication**

```bash
# GitHub Personal Access Token from https://github.com/settings/tokens
export GITHUB_TOKEN="your_github_token_here"

# NIST API Key from https://nvd.nist.gov/developers/request-an-api-key
export NIST_API_KEY="your_nist_api_key_here"
```

### Running the Server

**With virtual environment activated:**

```bash
# Make sure the virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or
# venv\Scripts\activate  # Windows

# Run the MCP server
python main.py
```

**Development mode (with MCP Inspector):**

```bash
# With venv activated
mcp dev main.py
```

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
    "risky-business": {
      "command": "/absolute/path/to/risky-business-mcp/venv/bin/python",
      "args": [
        "/absolute/path/to/risky-business-mcp/main.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "NIST_API_KEY": "your_nist_api_key_here"
      }
    }
  }
}
```

### Environment Variables

| Variable       | Description                                     | Required             |
| -------------- | ----------------------------------------------- | -------------------- |
| `GITHUB_TOKEN` | GitHub Personal Access Token for authentication | No (but recommended) |
| `NIST_API_KEY` | NIST NVD API key for increased rate limits      | No (optional)        |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Disclaimer**: This tool is for legitimate security research and educational purposes. Users are responsible for ensuring their use complies with applicable laws and GitHub's terms of service.