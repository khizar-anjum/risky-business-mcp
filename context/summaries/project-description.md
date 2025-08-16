Here is a complete product description you can use for your repository. It includes all the sections you requested.

-----

# 🤖 ThreatContext Engine

An AI agent that provides instant context and exploitability analysis for CVEs.

## The Problem

Security teams are overwhelmed by the constant flood of new CVE alerts. The most critical first step—determining if a new vulnerability is **actually exploitable** in the wild—is a manual and time-consuming process of searching through websites, databases, and code repositories. This manual friction slows down patching, prioritization, and response.

## Our Solution

**ThreatContext Engine** is an AI agent that automates this entire process. You give the agent a CVE, and within seconds, it provides a rich, actionable summary of the threat, including links to real Proof-of-Concept exploits. It turns hours of manual research into an instant decision-support tool.

## Demo

*(Pro-tip: After you have a working demo, take a screenshot of the final ASCII output from Claude Desktop and place it here. A visual is incredibly powerful.)*

`[Screenshot of the final ASCII ThreatCard will go here]`

## How It Works

The engine is built on a modern, agentic architecture. The agent (Claude Desktop) is given a goal, and it uses the **Model Context Protocol (MCP)** to discover and orchestrate the tools it needs to achieve that goal.

1.  **Goal:** The user gives the agent a goal, e.g., "Analyze CVE-2021-44228".
2.  **Tool Discovery:** The agent queries our mock MCP Server to ask what tools are available for tasks like `vulnerability-enrichment` and `exploit-search`.
3.  **Execution:** The MCP server provides a manifest of available tools. The agent then intelligently calls these tools in sequence—getting official data from NIST first, then searching for exploits on GitHub and Exploit-DB.
4.  **Synthesis & Presentation:** The agent takes the structured JSON data from all tools and passes it to its core LLM, using a specific prompt to generate the final, user-friendly ASCII dashboard.

### The Mock MCP Server

For this hackathon, our MCP server is a simple Flask/FastAPI application that acts as a tool directory. Its job is to respond to the agent's discovery requests with a JSON manifest describing the tools below.

### Tools Provided by the MCP Server

| Tool Name | Description for the Agent | Input Parameter |
| :--- | :--- | :--- |
| `get_cve_details` | "Fetches detailed information about a CVE from the official US National Vulnerability Database (NVD). Use this first to get the CVSS risk score and technical description." | `cve_id` (string) |
| `search_github_for_pocs` | "Searches GitHub code for files mentioning a CVE ID, which are likely to be Proof-of-Concept (PoC) exploit scripts. Returns a list of URLs." | `cve_id` (string) |
| `search_exploitdb` | "Uses the local 'searchsploit' tool to search the official Exploit-DB for curated exploits related to a CVE ID. Use this to find verified exploits." | `cve_id` (string) |

## The Prompt

To generate the final visualization, the agent uses the following prompt after it has collected the JSON data from its tools.

```
You are a world-class cybersecurity analyst presenting your findings in a clear, concise, and structured format. A tool has provided you with a JSON object containing data about a CVE. Your task is to transform this JSON into a clean ASCII report.

You MUST use the exact format provided in the example below. Do not add any conversational text, apologies, or explanations before or after the report.

Here is the JSON data:
{tool_json_data}

Here is the required ASCII format:

╔══════════════════════════════════════════════════════════════════════════════════╗
║ GITHUB EXPLOIT ANALYSIS: {cve_id}                                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

🔥 PoCs Found: {summary.total_results_found} total results on GitHub. Displaying top {summary.high_confidence_results}.

---[ RESULT 1 ]-------------------------------------------------------------------
  Repository: {results[0].repo_name}
  URL:        {results[0].url}

  Snippet:
  > {results[0].code_snippet_line1}
  > {results[0].code_snippet_line2}
```

## 🚀 Future Roadmap (Resources to Add Later)

This prototype is just the beginning. The MCP-based architecture makes it easy to extend the agent's capabilities by adding new tools.

  * [ ] **CISA KEV Catalog Tool:** Add a tool to check if the CVE is on the CISA Known Exploited Vulnerabilities list.
  * [ ] **Visualizations:** Implement the "Exploit Velocity" timeline and the "Behavioral Risk" chart in the final output.
  * [ ] **Proactive Monitoring:** Have the agent monitor RSS feeds or APIs for new CVEs and analyze them automatically.
  * [ ] **Code Analysis:** Give the agent a tool to perform a basic analysis of the PoC code itself to summarize the exploit technique.
  * [ ] **SIEM Integration:** Add a tool that can post the final summary to a webhook for a SIEM like Splunk or a chat app like Slack.
