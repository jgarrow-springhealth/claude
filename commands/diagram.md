The user wants to create a diagram. Follow these steps:

1. **Understand the requirements**:
   - If the user provides a file path, read the file first to find the ASCII art diagram
   - If the user pastes ASCII art directly, analyze it
   - If the user describes a new diagram, ask what type they want (flowchart, sequence diagram, state diagram, gantt chart, or decision tree) and what it should represent, unless they've already provided this information
   - For ASCII art conversions, determine what type of diagram it represents and what it's showing

2. **Generate Mermaid syntax**:
   - For ASCII art conversions: Interpret the ASCII diagram and convert it to equivalent Mermaid syntax, preserving the structure, flow, and relationships shown
   - For new diagrams: Create clean, well-structured Mermaid.js code for the diagram
   - For flowcharts, use LR (left-to-right) direction by default
   - Keep it simple unless the user requests detail
   - **IMPORTANT**: For line breaks in text labels (for Mermaid diagrams ONLY), use `\\n` (double backslash) NOT `\n` (single backslash). Single backslash will render as literal "\n" text instead of creating a line break

3. **Create the FigJam diagram**: Use the `mcp__figma-remote-mcp__generate_diagram` tool to create the diagram in FigJam.

4. **Provide both outputs**:
   - Show the FigJam link as a clickable markdown link
   - Display the Mermaid syntax in a code block with the language set to `mermaid`
   - Explain that they can:
     - Use the Mermaid code directly in Markdown files, documentation, or tools that support Mermaid
     - Import the Mermaid code into Excalidraw using Excalidraw's Mermaid integration
     - Edit the diagram in FigJam using the provided link

**Output format example:**

````
✓ Diagram created!

**FigJam:** [Diagram Name](figma-link-here)

**Mermaid Syntax:**
```mermaid
[mermaid code here]
````

You can use this Mermaid code in:

- Markdown files (GitHub, GitLab, Notion, etc.)
- Excalidraw (using the Mermaid to Excalidraw feature)
- Any Mermaid-compatible tool

```

**Important**: Always provide BOTH the FigJam link AND the Mermaid code block so the user has maximum flexibility.

---

## Usage Examples

**Convert ASCII art from a file:**
```

/diagram path/to/file.md

```

**Convert ASCII art directly:**
```

/diagram convert this ASCII:
[paste ASCII art here]

```

**Create new diagram:**
```

/diagram flowchart for deployment process
/diagram sequence diagram for payment flow

```

```
