"""
GitHub Repository Search MCP Server

This server provides tools to search GitHub repositories and includes
a prompt template for CVE-specific searches.
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any
import aiohttp
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

# Create the MCP server
mcp = FastMCP("GitHub Search Server")

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

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

@mcp.tool()
async def search_github_repositories(
    ctx: Context[ServerSession, None],
    query: str,
    sort: str = "best-match",
    order: str = "desc",
    per_page: int = 30,
    page: int = 1
) -> str:
    """
    Search GitHub repositories using the GitHub API.
    
    Args:
        query: The search query. Can include keywords and qualifiers like 'language:python', 'stars:>100', etc.
        sort: Sort results by 'stars', 'forks', 'help-wanted-issues', or 'updated'. Default is 'best-match'.
        order: Order results 'desc' (descending) or 'asc' (ascending). Default is 'desc'.
        per_page: Number of results per page (max 100). Default is 30.
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

if __name__ == "__main__":
    # Run the server
    mcp.run()