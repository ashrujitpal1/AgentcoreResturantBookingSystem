# Amazon Q Developer Configuration

This directory contains customization files that guide Amazon Q Developer when generating code for the Restaurant Booking System.

## Files

### `.amazonq/rules/project-rules.md`
**Purpose:** Project-level rules automatically applied to every chat and inline completion.

**Contains:**
- Architecture principles (LangGraph + Strands hybrid)
- SOLID principles enforcement
- Design patterns (Handoff, SAGA, Circuit Breaker)
- Code generation rules and templates
- Naming conventions
- Security requirements
- What NOT to do

**Usage:** Amazon Q automatically reads this file and applies rules to all code generation in this workspace.

### `.amazonq/customization.md`
**Purpose:** Detailed templates and examples for common patterns.

**Contains:**
- Import templates
- State schema templates
- Agent node templates
- Tool invocation patterns
- SAGA compensation patterns
- Circuit breaker implementation
- LLM provider abstraction
- Observability patterns

**Usage:** Reference this when asking Amazon Q to generate specific components.

## How to Use with Amazon Q

### 1. Automatic Application
Amazon Q automatically reads `.amazonq/rules/project-rules.md` for every request in this workspace. No action needed!

### 2. Explicit Reference
When you want Amazon Q to follow the production guide, use:

```
@workspace Generate a restaurant finder agent following the patterns in application-prod.md
```

Or reference specific sections:

```
@workspace Implement the booking agent with SAGA pattern as described in application-prod.md Layer 3
```

### 3. Inline Chat
When using inline chat (Cmd+I or Ctrl+I), Amazon Q will:
- Apply rules from `project-rules.md` automatically
- Follow patterns from `customization.md`
- Reference `application-prod.md` when mentioned

### 4. Example Prompts

**Generate an agent:**
```
Create a restaurant_finder_node following the Strands agent pattern with circuit breaker fallback
```

**Generate a workflow:**
```
Create the LangGraph workflow with entry_router, restaurant_finder, and booking_agent nodes
```

**Generate tool invocation:**
```
Create an idempotent tool call to bookATable with SAGA compensation
```

**Generate tests:**
```
Create unit tests for restaurant_finder_node testing circuit breaker fallback
```

## File Structure Created

```
.amazonq/
├── rules/
│   └── project-rules.md          # Auto-applied rules
├── customization.md               # Templates and patterns
└── README.md                      # This file
```

## Key Differences from GitHub Copilot

| Feature | GitHub Copilot | Amazon Q Developer |
|---------|----------------|-------------------|
| Rules file | `.github/copilot-instructions.md` | `.amazonq/rules/*.md` |
| Auto-apply | Manual reference | Automatic |
| Scope | Repository-level | Workspace-level |
| Format | Markdown | Markdown |
| Multiple files | Single file | Multiple files in `rules/` |

## Production Guide Reference

The main production guide is in:
```
application-prod.md
```

This comprehensive document contains:
- Complete architecture patterns
- Production-grade code examples
- Security and governance patterns
- Cost optimization strategies
- Testing strategies
- Deployment procedures

Amazon Q will reference this document when you use `@workspace` or explicitly mention it.

## Tips for Best Results

1. **Be Specific:** Reference exact sections from `application-prod.md`
   ```
   Generate code following the "SAGA Pattern Template" from application-prod.md
   ```

2. **Use @workspace:** This tells Amazon Q to consider all project files
   ```
   @workspace Create booking agent using patterns from application-prod.md
   ```

3. **Mention Principles:** Reference specific principles
   ```
   Create this agent following Single Responsibility Principle and using circuit breakers
   ```

4. **Reference Templates:** Point to specific templates
   ```
   Use the Agent Node Template from customization.md
   ```

## Updating Rules

When you update production patterns:

1. Update `application-prod.md` with new patterns
2. Update `.amazonq/rules/project-rules.md` with new rules
3. Update `.amazonq/customization.md` with new templates
4. Amazon Q will automatically use the updated rules

## Verification

To verify Amazon Q is using your rules:

1. Ask: "What are the project rules for this workspace?"
2. Amazon Q should reference the rules from `.amazonq/rules/project-rules.md`
3. Generate code and verify it follows the patterns

## Support

For more information:
- Amazon Q Documentation: https://docs.aws.amazon.com/amazonq/
- Project Guide: `application-prod.md`
- Architecture: `application.md`
- TODO List: `TODO.md`
