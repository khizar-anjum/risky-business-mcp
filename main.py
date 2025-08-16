"""
Risky Business AI MCP Server

This server provides tools to search GitHub repositories, query NIST NVD,
and access CISA's Known Exploited Vulnerabilities catalog.
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiohttp
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

# Create the MCP server
mcp = FastMCP("Risky Business AI MCP Server")

# API URLs
GITHUB_API_BASE = "https://api.github.com"
NIST_NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# Global cache for KEV data
kev_data_cache: Optional[Dict[str, Any]] = None

async def download_kev_data() -> Dict[str, Any]:
    """Download the CISA KEV data from the official feed"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(CISA_KEV_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Successfully downloaded KEV data: {data.get('count', 0)} vulnerabilities")
                    return data
                else:
                    print(f"Failed to download KEV data: HTTP {response.status}")
                    return {"vulnerabilities": [], "count": 0}
        except Exception as e:
            print(f"Error downloading KEV data: {e}")
            return {"vulnerabilities": [], "count": 0}

async def initialize_kev_data():
    """Initialize KEV data cache on server startup"""
    global kev_data_cache
    print("Downloading CISA Known Exploited Vulnerabilities catalog...")
    kev_data_cache = await download_kev_data()
    print(f"KEV data initialized with {kev_data_cache.get('count', 0)} entries")

async def make_github_request(
    session: aiohttp.ClientSession,
    endpoint: str,
    params: Dict[str, Any],
    token: Optional[str] = None
) -> Dict[str, Any]:
    """Make a request to the GitHub API"""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Add authentication token if available
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API_BASE}{endpoint}"

    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 200:
            return await response.json()
        elif response.status == 422:
            raise ValueError("Invalid search query or validation failed")
        elif response.status == 503:
            raise RuntimeError("GitHub API service unavailable")
        else:
            response.raise_for_status()

async def make_nist_request(
    session: aiohttp.ClientSession,
    cve_id: str,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Make a request to the NIST NVD API"""
    headers = {
        "Accept": "application/json"
    }
    
    # Add API key if available (increases rate limit)
    if api_key:
        headers["apiKey"] = api_key
    
    params = {
        "cveId": cve_id
    }
    
    async with session.get(NIST_NVD_API_BASE, headers=headers, params=params) as response:
        if response.status == 200:
            data = await response.json()
            # Check if any vulnerabilities were found
            if data.get("totalResults", 0) > 0:
                return data
            return None
        elif response.status == 403:
            raise RuntimeError("NIST API rate limit exceeded. Consider using an API key.")
        elif response.status == 404:
            return None
        else:
            response.raise_for_status()

@mcp.tool()
async def search_github_repositories(
    ctx: Context[ServerSession, None],
    query: str,
    sort: str = "best-match",
    order: str = "desc",
    per_page: int = 5,
    page: int = 1
) -> str:
    """
    Search GitHub repositories using the GitHub API.

    Args:
        query: The search query. Can include keywords and qualifiers like 'language:python', 'stars:>100', etc.
        sort: Sort results by 'stars', 'forks', 'help-wanted-issues', or 'updated'. Default is 'best-match'.
        order: Order results 'desc' (descending) or 'asc' (ascending). Default is 'desc'.
        per_page: Number of results per page (max 100). Default is 5.
        page: Page number of results to fetch. Default is 1.

    Returns:
        JSON string containing repository search results with URLs for accessing the repositories.
    """
    await ctx.info(f"Searching GitHub repositories for: {query}")

    # Validate parameters
    if per_page > 100 or per_page < 1:
        raise ValueError("per_page must be between 1 and 100")

    if page < 1:
        raise ValueError("page must be greater than 0")

    valid_sorts = ["stars", "forks", "help-wanted-issues", "updated"]
    if sort != "best-match" and sort not in valid_sorts:
        raise ValueError(f"sort must be 'best-match' or one of: {', '.join(valid_sorts)}")

    valid_orders = ["desc", "asc"]
    if order not in valid_orders:
        raise ValueError(f"order must be one of: {', '.join(valid_orders)}")

    # Prepare API parameters
    params = {
        "q": query,
        "per_page": per_page,
        "page": page
    }

    # Only add sort/order if not using best-match
    if sort != "best-match":
        params["sort"] = sort
        params["order"] = order

    try:
        # Get GitHub token from environment (optional)
        github_token = os.getenv("GITHUB_TOKEN")

        async with aiohttp.ClientSession() as session:
            await ctx.info("Making request to GitHub API...")

            response_data = await make_github_request(
                session, "/search/repositories", params, github_token
            )

            await ctx.info(f"Found {response_data['total_count']} repositories")

            # Extract relevant information for each repository
            repositories = []
            for item in response_data.get("items", []):
                repo_info = {
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item.get("description", "No description"),
                    "html_url": item["html_url"],  # Main repository URL
                    "clone_url": item["clone_url"],  # Git clone URL
                    "owner": {
                        "login": item["owner"]["login"],
                        "html_url": item["owner"]["html_url"]
                    },
                    "language": item.get("language", "Unknown"),
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "private": item["private"],
                    "archived": item.get("archived", False),
                    "license": item.get("license", {}).get("name") if item.get("license") else None
                }
                repositories.append(repo_info)

            # Prepare result summary
            result = {
                "search_query": query,
                "total_count": response_data["total_count"],
                "incomplete_results": response_data["incomplete_results"],
                "page": page,
                "per_page": per_page,
                "repositories": repositories
            }

            await ctx.info(f"Successfully retrieved {len(repositories)} repositories from page {page}")

            return json.dumps(result, indent=2)

    except aiohttp.ClientError as e:
        await ctx.error(f"Network error while accessing GitHub API: {e}")
        raise RuntimeError(f"Failed to connect to GitHub API: {e}")
    except ValueError as e:
        await ctx.error(f"Invalid request: {e}")
        raise e
    except Exception as e:
        await ctx.error(f"Unexpected error during GitHub search: {e}")
        raise RuntimeError(f"GitHub search failed: {e}")

@mcp.tool()
async def get_cve_from_nist(
    ctx: Context[ServerSession, None],
    cve_id: str
) -> str:
    """
    Retrieve CVE information from NIST NVD (National Vulnerability Database).
    
    Args:
        cve_id: The CVE identifier (e.g., "CVE-2023-1234" or "2023-1234")
    
    Returns:
        JSON string containing CVSS score, severity, CWE, description, and CPE configuration.
        Returns a graceful error message if CVE is not found.
    """
    # Normalize CVE ID format
    cve_id = cve_id.upper().strip()
    if not cve_id.startswith("CVE-"):
        cve_id = f"CVE-{cve_id}"
    
    # Validate CVE format (CVE-YYYY-NNNN or CVE-YYYY-NNNNN+)
    import re
    if not re.match(r'^CVE-\d{4}-\d{4,}$', cve_id):
        return json.dumps({
            "status": "error",
            "message": f"Invalid CVE format: {cve_id}. Expected format: CVE-YYYY-NNNN"
        }, indent=2)
    
    await ctx.info(f"Looking up {cve_id} in NIST NVD...")
    
    try:
        # Get NIST API key from environment (optional)
        nist_api_key = os.getenv("NIST_API_KEY")
        
        async with aiohttp.ClientSession() as session:
            response_data = await make_nist_request(session, cve_id, nist_api_key)
            
            if response_data is None:
                await ctx.info(f"CVE {cve_id} not found in NIST NVD")
                return json.dumps({
                    "status": "not_found",
                    "message": f"CVE {cve_id} not found in NIST National Vulnerability Database",
                    "cve_id": cve_id
                }, indent=2)
            
            # Extract the vulnerability data
            vulnerabilities = response_data.get("vulnerabilities", [])
            if not vulnerabilities:
                return json.dumps({
                    "status": "not_found",
                    "message": f"No vulnerability data found for {cve_id}",
                    "cve_id": cve_id
                }, indent=2)
            
            cve_item = vulnerabilities[0].get("cve", {})
            
            # Extract CVSS scores and severity
            cvss_data = {}
            metrics = cve_item.get("metrics", {})
            
            # Check for CVSS v3.1
            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                cvss_v31 = metrics["cvssMetricV31"][0]
                cvss_data["cvss_v31"] = {
                    "score": cvss_v31.get("cvssData", {}).get("baseScore"),
                    "severity": cvss_v31.get("cvssData", {}).get("baseSeverity"),
                    "vector": cvss_v31.get("cvssData", {}).get("vectorString")
                }
            
            # Check for CVSS v3.0
            if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                cvss_v30 = metrics["cvssMetricV30"][0]
                cvss_data["cvss_v30"] = {
                    "score": cvss_v30.get("cvssData", {}).get("baseScore"),
                    "severity": cvss_v30.get("cvssData", {}).get("baseSeverity"),
                    "vector": cvss_v30.get("cvssData", {}).get("vectorString")
                }
            
            # Check for CVSS v2.0
            if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                cvss_v2 = metrics["cvssMetricV2"][0]
                cvss_data["cvss_v2"] = {
                    "score": cvss_v2.get("cvssData", {}).get("baseScore"),
                    "severity": cvss_v2.get("baseSeverity"),
                    "vector": cvss_v2.get("cvssData", {}).get("vectorString")
                }
            
            # Extract CWE (Common Weakness Enumeration)
            cwe_list = []
            weaknesses = cve_item.get("weaknesses", [])
            for weakness in weaknesses:
                for desc in weakness.get("description", []):
                    if desc.get("lang") == "en":
                        cwe_list.append(desc.get("value"))
            
            # Extract description
            description = ""
            descriptions = cve_item.get("descriptions", [])
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            
            # Extract CPE configurations (affected products)
            cpe_configurations = []
            configurations = cve_item.get("configurations", [])
            for config in configurations:
                nodes = config.get("nodes", [])
                for node in nodes:
                    cpe_matches = node.get("cpeMatch", [])
                    for cpe in cpe_matches:
                        if cpe.get("vulnerable"):
                            cpe_info = {
                                "cpe23Uri": cpe.get("criteria"),
                                "versionStartIncluding": cpe.get("versionStartIncluding"),
                                "versionEndExcluding": cpe.get("versionEndExcluding"),
                                "versionEndIncluding": cpe.get("versionEndIncluding")
                            }
                            # Remove None values
                            cpe_info = {k: v for k, v in cpe_info.items() if v is not None}
                            cpe_configurations.append(cpe_info)
            
            # Extract references
            references = []
            for ref in cve_item.get("references", []):
                references.append({
                    "url": ref.get("url"),
                    "source": ref.get("source"),
                    "tags": ref.get("tags", [])
                })
            
            # Build the result
            result = {
                "status": "found",
                "cve_id": cve_item.get("id"),
                "published": cve_item.get("published"),
                "last_modified": cve_item.get("lastModified"),
                "description": description,
                "cvss_scores": cvss_data,
                "cwe": cwe_list,
                "cpe_configurations": cpe_configurations[:10],  # Limit to first 10 for readability
                "references": references[:5],  # Limit to first 5 references
                "source_identifier": cve_item.get("sourceIdentifier"),
                "vuln_status": cve_item.get("vulnStatus")
            }
            
            # Determine the primary CVSS score and severity to highlight
            primary_cvss = None
            if "cvss_v31" in cvss_data:
                primary_cvss = cvss_data["cvss_v31"]
                result["primary_severity"] = primary_cvss["severity"]
                result["primary_score"] = primary_cvss["score"]
            elif "cvss_v30" in cvss_data:
                primary_cvss = cvss_data["cvss_v30"]
                result["primary_severity"] = primary_cvss["severity"]
                result["primary_score"] = primary_cvss["score"]
            elif "cvss_v2" in cvss_data:
                primary_cvss = cvss_data["cvss_v2"]
                result["primary_severity"] = primary_cvss["severity"]
                result["primary_score"] = primary_cvss["score"]
            
            await ctx.info(f"Successfully retrieved data for {cve_id}")
            
            return json.dumps(result, indent=2)
            
    except aiohttp.ClientError as e:
        await ctx.error(f"Network error while accessing NIST NVD API: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to connect to NIST NVD API: {str(e)}",
            "cve_id": cve_id
        }, indent=2)
    except Exception as e:
        await ctx.error(f"Unexpected error during NIST lookup: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "cve_id": cve_id
        }, indent=2)

def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse a GitHub repository URL to extract owner and repo name.
    
    Args:
        url: GitHub repository URL (e.g., "https://github.com/owner/repo" or "https://github.com/owner/repo.git")
    
    Returns:
        Tuple of (owner, repo) extracted from the URL
    
    Raises:
        ValueError: If the URL is not a valid GitHub repository URL
    """
    import re
    
    # Clean up the URL
    url = url.strip().rstrip('/')
    
    # Remove .git suffix if present
    if url.endswith('.git'):
        url = url[:-4]
    
    # Match GitHub URL patterns
    patterns = [
        r'https?://github\.com/([^/]+)/([^/]+)',
        r'git@github\.com:([^/]+)/([^/]+)',
        r'github\.com/([^/]+)/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            return owner, repo
    
    raise ValueError(f"Invalid GitHub URL format: {url}")

@mcp.tool()
async def list_github_repository_files(
    ctx: Context[ServerSession, None],
    repo_url: str,
    branch: str = "main"
) -> str:
    """
    List all files in a GitHub repository using the Git Trees API.
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
        branch: Branch name to get files from (default: "main")
    
    Returns:
        JSON string containing the list of all files in the repository
    """
    await ctx.info(f"Listing files from repository: {repo_url}")
    
    try:
        # Parse the GitHub URL to get owner and repo
        owner, repo = parse_github_url(repo_url)
        await ctx.info(f"Parsed repository: {owner}/{repo}")
        
        # Get GitHub token from environment (optional)
        github_token = os.getenv("GITHUB_TOKEN")
        
        async with aiohttp.ClientSession() as session:
            # First, try to get the repository info to validate it exists
            repo_endpoint = f"/repos/{owner}/{repo}"
            await ctx.info(f"Validating repository exists...")
            
            try:
                await make_github_request(session, repo_endpoint, {}, github_token)
            except Exception as e:
                if "404" in str(e):
                    raise ValueError(f"Repository {owner}/{repo} not found or not accessible")
                raise e
            
            # Get the tree with all files recursively
            tree_endpoint = f"/repos/{owner}/{repo}/git/trees/{branch}"
            params = {"recursive": "1"}
            
            await ctx.info(f"Fetching file tree for branch '{branch}'...")
            
            response_data = await make_github_request(
                session, tree_endpoint, params, github_token
            )
            
            # Extract file information
            files = []
            directories = []
            
            for item in response_data.get("tree", []):
                item_info = {
                    "path": item["path"],
                    "type": item["type"],
                    "size": item.get("size"),
                    "sha": item["sha"],
                    "url": item.get("url")
                }
                
                if item["type"] == "blob":  # File
                    files.append(item_info)
                elif item["type"] == "tree":  # Directory
                    directories.append(item_info)
            
            # Prepare result summary
            result = {
                "repository": {
                    "owner": owner,
                    "name": repo,
                    "url": repo_url,
                    "branch": branch
                },
                "summary": {
                    "total_files": len(files),
                    "total_directories": len(directories),
                    "total_items": len(files) + len(directories)
                },
                "files": files,
                "directories": directories
            }
            
            await ctx.info(f"Successfully retrieved {len(files)} files and {len(directories)} directories")
            
            return json.dumps(result, indent=2)
            
    except ValueError as e:
        await ctx.error(f"Invalid input: {e}")
        raise e
    except aiohttp.ClientError as e:
        await ctx.error(f"Network error while accessing GitHub API: {e}")
        raise RuntimeError(f"Failed to connect to GitHub API: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error during file listing: {e}")
        raise RuntimeError(f"GitHub file listing failed: {e}")

@mcp.prompt()
def cve_repository_search(cve_number: str, include_poc: bool = True) -> str:
    """
    Generate a search prompt for finding GitHub repositories related to a specific CVE.

    Args:
        cve_number: The CVE number (e.g., "CVE-2023-1234")
        include_poc: Whether to include PoC-specific search terms

    Returns:
        A formatted prompt for searching CVE-related repositories
    """
    # Clean CVE number format
    cve_clean = cve_number.upper().strip()
    if not cve_clean.startswith("CVE-"):
        cve_clean = f"CVE-{cve_clean}"

    # Base search terms
    search_terms = [cve_clean]

    # Add PoC-specific terms if requested
    if include_poc:
        poc_terms = ["poc", "proof of concept", "exploit", "vulnerability", "demo"]
        search_terms.extend(poc_terms)

    # Additional qualifiers for better results
    qualifiers = [
        "in:name,description,readme",  # Search in multiple fields
        "sort:updated",  # Get recently updated repos
        "order:desc"  # Most recent first
    ]

    prompt = f"""
Use the search_github_repositories tool to find repositories related to {cve_clean}.

Recommended search strategies:

1. **Primary search**: Search for the exact CVE number
   Query: "{cve_clean}"

2. **PoC-focused search**: Include proof-of-concept terms
   Query: "{cve_clean} poc OR exploit OR vulnerability"

3. **Broader search**: Include related terms
   Query: "({cve_clean} OR {cve_clean.replace('-', '')}) AND (poc OR exploit OR vulnerability OR demo)"

4. **Language-specific search**: If you know the affected technology
   Query: "{cve_clean} language:python" (replace python with relevant language)

5. **Recent activity**: Focus on recently updated repositories
   Query: "{cve_clean} pushed:>2023-01-01"

**Important notes:**
- Look for repositories with clear documentation and recent activity
- Check the repository description and README for PoC indicators
- Pay attention to the repository owner's credibility
- Verify that the repository actually contains relevant exploit code
- Be cautious of repositories that might contain malicious code

**What to look for in results:**
- Repository names containing the CVE number
- Descriptions mentioning "proof of concept", "exploit", or "vulnerability"
- Recent commits or updates
- Clear documentation explaining the vulnerability
- Code that demonstrates the security issue

The search will return repository URLs that you can access to examine the PoC code.
"""

    return prompt

@mcp.prompt()
def advanced_cve_search_strategies() -> str:
    """
    Generate advanced search strategies for CVE research on GitHub.

    Returns:
        A comprehensive guide for advanced CVE repository searching
    """
    return """
Advanced GitHub CVE Search Strategies

Use these search patterns with the search_github_repositories tool for comprehensive CVE research:

**1. Multi-term CVE Search**
- Query: "CVE-2023-1234 OR CVE20231234 OR 2023-1234"
- Rationale: Different naming conventions used by researchers

**2. Exploit Development Stages**
- Query: "CVE-2023-1234 AND (poc OR exploit OR weaponized OR 0day)"
- Rationale: Find repositories at different stages of exploit development

**3. Security Research Context**
- Query: "CVE-2023-1234 AND (analysis OR research OR writeup OR blog)"
- Rationale: Find detailed security research and analysis

**4. Technology-Specific Searches**
- Web: "CVE-2023-1234 language:javascript OR language:php OR language:html"
- System: "CVE-2023-1234 language:c OR language:cpp OR language:python"
- Mobile: "CVE-2023-1234 android OR ios OR mobile"

**5. Timeline-Based Searches**
- Recent: "CVE-2023-1234 pushed:>2023-06-01"
- Historical: "CVE-2023-1234 created:2023-01-01..2023-12-31"

**6. Quality Indicators**
- Query: "CVE-2023-1234 stars:>5 forks:>2"
- Rationale: Find well-regarded repositories with community validation

**7. Academic and Professional Sources**
- Query: "CVE-2023-1234 user:security-org OR user:university"
- Rationale: Find repositories from credible security organizations

**8. Vulnerability Scanners and Tools**
- Query: "CVE-2023-1234 AND (scanner OR detection OR nessus OR nuclei)"
- Rationale: Find detection rules and scanning tools

**Search Result Evaluation Criteria:**
✅ Repository has clear documentation
✅ Recent commit activity
✅ Verified or credible author
✅ Proper attribution and references
✅ Clear explanation of the vulnerability
✅ Responsible disclosure practices

⚠️ Red Flags:
❌ No documentation or unclear purpose
❌ Suspicious or anonymous authors
❌ Malicious-looking code patterns
❌ Lack of proper attribution
❌ Encouragement of malicious use

**Remember**: Always verify the authenticity and safety of any PoC code before use.
"""

@mcp.resource("kev://cisa/catalog")
async def get_kev_resource() -> str:
    """
    Expose the CISA Known Exploited Vulnerabilities catalog as a resource.
    This provides the full KEV dataset for reference.
    """
    if kev_data_cache is None:
        await initialize_kev_data()
    
    return json.dumps(kev_data_cache, indent=2)

@mcp.tool()
async def search_kev(
    ctx: Context[ServerSession, None],
    query: str,
    field: str = "all",
    max_results: int = 10
) -> str:
    """
    Search the CISA Known Exploited Vulnerabilities (KEV) catalog.
    
    Args:
        query: Search query (CVE ID, vendor name, product name, or keyword)
        field: Field to search in - "all", "cve_id", "vendor", "product", "vulnerability_name", "date_added"
        max_results: Maximum number of results to return (default 10, max 50)
    
    Returns:
        JSON string containing matching KEV entries with exploitation details.
    """
    if kev_data_cache is None:
        await initialize_kev_data()
    
    await ctx.info(f"Searching KEV catalog for: {query}")
    
    # Validate parameters
    if max_results > 50:
        max_results = 50
    
    valid_fields = ["all", "cve_id", "vendor", "product", "vulnerability_name", "date_added"]
    if field not in valid_fields:
        return json.dumps({
            "status": "error",
            "message": f"Invalid field. Must be one of: {', '.join(valid_fields)}"
        }, indent=2)
    
    query_lower = query.lower()
    results = []
    
    # Search through vulnerabilities
    for vuln in kev_data_cache.get("vulnerabilities", []):
        match = False
        
        if field == "all":
            # Search across all text fields
            searchable_text = " ".join([
                str(vuln.get("cveID", "")),
                str(vuln.get("vendorProject", "")),
                str(vuln.get("product", "")),
                str(vuln.get("vulnerabilityName", "")),
                str(vuln.get("shortDescription", "")),
                str(vuln.get("notes", ""))
            ]).lower()
            match = query_lower in searchable_text
        elif field == "cve_id":
            cve_id = vuln.get("cveID", "").lower()
            match = query_lower in cve_id or cve_id in query_lower
        elif field == "vendor":
            match = query_lower in vuln.get("vendorProject", "").lower()
        elif field == "product":
            match = query_lower in vuln.get("product", "").lower()
        elif field == "vulnerability_name":
            match = query_lower in vuln.get("vulnerabilityName", "").lower()
        elif field == "date_added":
            match = query in vuln.get("dateAdded", "")
        
        if match:
            results.append({
                "cve_id": vuln.get("cveID"),
                "vendor": vuln.get("vendorProject"),
                "product": vuln.get("product"),
                "vulnerability_name": vuln.get("vulnerabilityName"),
                "date_added": vuln.get("dateAdded"),
                "short_description": vuln.get("shortDescription"),
                "required_action": vuln.get("requiredAction"),
                "due_date": vuln.get("dueDate"),
                "known_ransomware_use": vuln.get("knownRansomwareCampaignUse"),
                "notes": vuln.get("notes")
            })
            
            if len(results) >= max_results:
                break
    
    # Sort results by date_added (most recent first)
    results.sort(key=lambda x: x.get("date_added", ""), reverse=True)
    
    response = {
        "status": "success",
        "query": query,
        "field": field,
        "total_results": len(results),
        "results": results
    }
    
    if len(results) == 0:
        response["message"] = f"No vulnerabilities found matching '{query}' in KEV catalog"
    else:
        await ctx.info(f"Found {len(results)} matching vulnerabilities in KEV catalog")
    
    return json.dumps(response, indent=2)

if __name__ == "__main__":
    # Run the server (KEV data will be loaded on first access)
    mcp.run()
