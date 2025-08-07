## Overview & Daily Structure

**Daily 2 Hours:**

- 09:00-09:30: Theory & Concepts (30 min)
- 09:30-11:00: Practical Exercises (90 min)
- 17:00-17:15: Reflection & Documentation (15 min)

**Weekly Goals:**

- Week 1: Master Claude Code Fundamentals
- Week 2: Advanced Workflows & Multi-Agent Systems
- Week 3: Sub-Agents & Parallel Development
- Week 4: Expert Optimization & Professional Templates

---

## Week 1: Foundation & Setup (Days 1-7)

### Day 1: Installation & First Steps

**09:00-09:30 Theory:**

- What is Agentic Coding vs. traditional programming
- Claude Code Philosophy: Terminal-based AI system
- Differences from Cursor, GitHub Copilot, ChatGPT

**09:30-11:00 Practice:**

```bash
# Installation
npm install -g @anthropic-ai/claude-code

# Configure environment
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_LOG=debug
export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true

# First project
mkdir claude-bootcamp-project
cd claude-bootcamp-project
claude /init
```

**Concrete Tasks:**

1. Create simple "Hello World" application in your preferred language
2. Have Claude generate a README.md for your project
3. Test Git integration: Commit and push

**17:00-17:15 Reflection:**

- What was surprising about Claude Code?
- How does it differ from other AI tools?

### Day 2: CLAUDE.md Mastery & Priming

**09:00-09:30 Theory:**

- **Priming Concept**: "Read these files, but don't write code yet"
- Memory Hierarchy: User vs. Project Level
- Context Engineering Principles

**09:30-11:00 Practice:**
Create your first CLAUDE.md:

```markdown
# Project: [Your Project Name]

## Project Overview

[Description of your project - can be Web App, CLI Tool, API, etc.]

## Development Environment

- **Language**: [Python/JavaScript/Go/Rust/etc.]
- **Framework**: [If relevant: React/Express/Django/etc.]
- **Testing**: [pytest/jest/go test/etc.]
- **Code Style**: [Black/Prettier/gofmt/etc.]

## Code Standards

- Use [Language-specific] Best Practices
- Always write tests for new features
- Document complex logic
- English comments preferred

## Special Instructions

- Ask when requirements are unclear
- Implement error handling
- Consider performance implications
- Use modern language features

## Context Files

@docs/architecture.md
@README.md
```

**Concrete Tasks:**

1. Create project-specific CLAUDE.md
2. Test priming: "Analyze my codebase, but don't write anything yet"
3. Have Claude understand your project and suggest improvements

### Day 3: Slash Commands Library

**09:30-11:00 Practice:**
Create 5 essential commands:

```markdown
# .claude/commands/implement.md

Implement feature: $ARGUMENTS

## Steps:

1. Analyze requirements
2. Plan architecture
3. Write tests (if TDD)
4. Implement core functionality
5. Add error handling
6. Document code
7. Test manually

Follow project standards from CLAUDE.md
```

```markdown
# .claude/commands/review.md

Code review for: $ARGUMENTS

## Review Checklist:

- [ ] Code quality and readability
- [ ] Performance considerations
- [ ] Security vulnerabilities
- [ ] Test coverage
- [ ] Documentation
- [ ] Error handling
- [ ] Best practices

Provide specific improvement suggestions.
```

```markdown
# .claude/commands/refactor.md

Refactor code: $ARGUMENTS

## Refactoring Process:

1. Understand current implementation
2. Identify improvement opportunities
3. Create tests (if not present)
4. Refactor incrementally
5. Verify tests
6. Document changes

Keep functionality identical.
```

```markdown
# .claude/commands/debug.md

Debug problem: $ARGUMENTS

## Debug Strategy:

1. Reproduce the problem
2. Isolate the cause
3. Analyze logs/stack traces
4. Test hypotheses
5. Implement fix
6. Verify solution
7. Add tests (regression)

Document the debugging process.
```

```markdown
# .claude/commands/optimize.md

Optimize performance: $ARGUMENTS

## Optimization Areas:

- Algorithm efficiency
- Memory usage
- I/O operations
- Caching strategies
- Concurrent/parallel processing

Measure performance before and after optimization.
```

**Concrete Tasks:**

1. Create all 5 commands
2. Test each command with real scenarios
3. Document which commands for which situations

### Day 4: Extended Thinking & Planning

**09:00-09:30 Theory:**

- Thinking Levels: "think" < "think hard" < "think harder" < "ultrathink"
- When to use each level
- Cost vs. Quality trade-offs

**09:30-11:00 Practice:**

```bash
# Basic Planning
> "Plan the implementation of this function step by step"

# Enhanced Planning
> "Think hard about the best architecture for this system"

# Maximum Reasoning
> "Ultrathink about the security implications and edge cases"
```

**Concrete Tasks:**

1. Test all thinking levels with a complex architectural decision
2. Compare quality of outputs
3. Create planning template for your project

### Day 5: Git Integration & Workflows

**09:30-11:00 Practice:**

```bash
# GitHub CLI Setup
gh auth login

# Git Hooks
git config core.hooksPath .githooks
```

Create Git Commands:

```markdown
# .claude/commands/git/commit-smart.md

Analyze changes and create structured commit:

## Commit Process:

1. Review: `git diff --staged`
2. Determine type: feat/fix/docs/style/refactor/test
3. Message format: `type(scope): description`
4. Detailed description
5. Mention breaking changes
6. Add issue references

Create meaningful commit automatically.
```

**Concrete Tasks:**

1. Integrate GitHub CLI
2. Create automated commit workflows
3. Test pull request creation with Claude

### Day 6: Context Management & Token Optimization

**09:00-09:30 Theory:**

- Understanding context windows
- When to use /clear vs. /compact
- Cost monitoring strategies

**09:30-11:00 Practice:**

```markdown
# .claude/commands/manage/session.md

Session Management: $ARGUMENTS

## Options:

- **clear**: Complete restart (new features)
- **compact**: Compress context (ongoing work)
- **checkpoint**: Git commit + summary

## Decision Guide:

- Context >80% → compact
- New topic → clear
- Important milestone → checkpoint

Optimize session for efficiency.
```

**Concrete Tasks:**

1. Implement cost tracking
2. Test different context management strategies
3. Create budget alerts

### Day 7: Week 1 Integration & Project Starter Template

**09:30-11:00 Practice:**
**Project: Complete Application of Your Choice + Starter Template**

Create a complete application using everything learned:

- CLI Tool with subcommands
- Web API with multiple endpoints
- Desktop App with GUI
- Mobile App with multiple screens
- Data Processing Pipeline
- Game or Simulation

**Requirements:**

1. Complete CLAUDE.md configuration
2. 10+ Custom slash commands
3. Git integration with AI commits
4. Test suite with high coverage
5. Documentation and README
6. Error handling and logging

**Create Your Project Starter Template:**

````bash
#!/bin/bash
# create-claude-project.sh

PROJECT_NAME=$1
TEMPLATE_TYPE=${2:-"web"} # web, cli, api, mobile, data

echo "🚀 Creating Claude Code project: $PROJECT_NAME"

# Create directory structure
mkdir -p "$PROJECT_NAME"/{src,tests,docs,.claude/{commands,templates}}
cd "$PROJECT_NAME"

# Initialize git
git init

# Create CLAUDE.md template
cat > CLAUDE.md << 'EOF'
# Project: [PROJECT_NAME]

## Project Overview
[Brief description of the project purpose and goals]

## Development Environment
- **Language**: [Your preferred language]
- **Framework**: [Framework if applicable]
- **Testing**: [Testing framework]
- **Code Style**: [Style guide/formatter]

## Code Standards
- Write clean, maintainable code
- Follow [language] best practices
- Test coverage minimum 80%
- Document all public APIs
- Use meaningful variable/function names
- Handle errors gracefully

## Architecture Principles
- [Add your principles]
- Keep it simple (KISS)
- Don't repeat yourself (DRY)
- Single responsibility principle

## Special Instructions
- Ask for clarification when requirements are ambiguous
- Consider performance implications
- Think about edge cases
- Validate inputs
- Log important operations

## Context Files
@README.md
@docs/architecture.md
@package.json (or equivalent)
EOF

# Create essential commands
cat > .claude/commands/start.md << 'EOF'
Start new feature: $ARGUMENTS

## Process:
1. Understand requirements
2. Check existing code patterns
3. Plan implementation approach
4. Create tests first (TDD)
5. Implement incrementally
6. Document as you go

Follow all project standards.
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
venv/
vendor/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Logs
*.log

# OS
.DS_Store
Thumbs.db
EOF

# Create README template
cat > README.md << 'EOF'
# [PROJECT_NAME]

## Overview
[Project description]

## Features
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## Installation
```bash
# Installation steps
````

## Usage

```bash
# Usage examples
```

## Development

```bash
# Development setup
```

## Testing

```bash
# Run tests
```

## Contributing

[Contributing guidelines]

## License

[License information]
EOF

echo "✅ Project structure created!"
echo "📁 Directory structure:"
tree -a -I '.git'

echo ""
echo "🎯 Next steps:"
echo "1. cd $PROJECT_NAME"
echo "2. Edit CLAUDE.md with your project specifics"
echo "3. claude /init"
echo "4. Start developing with Claude Code!"

```

```
