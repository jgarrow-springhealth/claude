# Bug Investigator Plugin

Investigate and diagnose bugs in SpringCare applications. Coordinates parallel subagents to gather data from multiple sources, then synthesizes findings into a Confluence RCA document.

## TODO

- [ ] Improve on Datadog research in the `data` agent. At the time of creating this plugin, we did not yet have access to the Datadog MCP.
- [ ] Improve Playwright implementation. It's not super reliable, as it relies on good seed data to exist in dev. And I'm also not loving the screen recording side of the implementation here. Lots of room for improvement in the automated bug reproduction side of things.

## What it does

When you report a bug (via Jira ticket URL, Slack post link, or description), the plugin:

1. Parses the bug report and extracts identifiers
2. Launches parallel investigations across data sources (Snowflake, Datadog, Mixpanel), Slack history, and the codebase (GitHub + LaunchDarkly)
3. Attempts to reproduce the bug on dev using Playwright
4. Synthesizes all findings into a Confluence RCA page and comments on the Jira ticket

## Installation

```bash
claude plugin marketplace add SpringCare/ai-registry@marketplace
claude plugin install bug-investigator
```

## Usage

Full investigation:

```bash
/bug-investigator:investigate https://springhealth.atlassian.net/browse/ENG-1234
```

Or just describe the bug and the skill will trigger automatically.

Individual agents can be invoked directly:

```txt
@"bug-investigator:data" pull signals for ENG-5678
@"bug-investigator:slack" anything about session note failures this week?
@"bug-investigator:code" find the benefit limit code in Member Portal
@"bug-investigator:reproduce" members get a 500 on intake submit. Role: member.
```

## Prerequisites

### GitHub plugin (required, not bundled)

The `code` agent uses the GitHub MCP server to search repos, read code, and check commits. This plugin does **not** bundle the GitHub MCP because it requires a GitHub App installation tied to your org.

Install it from the official marketplace:

```bash
/plugin install github
```

Follow the prompts to authenticate with your GitHub account.

### Bundled MCP servers

The following MCP servers are bundled with this plugin via `.mcp.json`. If you already have any of these configured, your existing configuration takes precedence.

| MCP Server                        | Used by           | Purpose                                  |
| --------------------------------- | ----------------- | ---------------------------------------- |
| Atlassian                         | investigate skill | Read Jira tickets, create Confluence RCA |
| Slack                             | slack agent       | Search Slack for related discussions     |
| Datadog                           | data agent        | Query logs and traces                    |
| Mixpanel                          | data agent        | Query product analytics events           |
| Playwright                        | reproduce agent   | Browser automation for bug reproduction  |
| LaunchDarkly (feature management) | code agent        | Check feature flag state                 |

Most of these use OAuth and will prompt you to authenticate on first use.

## Installation

Register the Spring Health marketplace (one time):

```bash
claude plugin marketplace add SpringCare/ai-registry@marketplace
```

Then install the plugin:

```bash
claude plugin install bug-investigator
```

Or load from a local path for development/testing:

```bash
claude --plugin-dir /path/to/bug-investigator-plugin
```

## Components

- **Skill:** `investigate` -- orchestrates the full investigation workflow
- **Agents:**
  - `data` -- queries Snowflake, Datadog, Mixpanel
  - `code` -- searches GitHub repos, checks LaunchDarkly flags
  - `slack` -- searches Slack for related discussions
  - `reproduce` -- reproduces bugs on dev environments via Playwright
