# GitHub Copilot Instructions: LLM Implementation Guide

## Implementation Algorithm

```
IF project needs Copilot instructions:
  1. Enable VS Code setting: github.copilot.chat.codeGeneration.useInstructionFiles = true
  2. Create .github/copilot-instructions.md
  3. IF file > 200 lines: split into max 3 specialized files
  4. Test: verify instructions appear in Copilot References
```

## Required Setup

```json
// VS Code settings.json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true
}
```

## Decision Matrix

| Use Case | File Path | Template | Status |
|----------|-----------|----------|---------|
| All projects | `.github/copilot-instructions.md` | Template A | ✅ Reliable |
| File-specific rules | `.github/instructions/[name].instructions.md` | Template B | ⚠️ Experimental |
| Cross-references | Markdown links between files | Template C | ✅ Reliable |

## Template A: Single File (Primary)

```markdown
# [PROJECT_NAME] Instructions

## Context
You are a [ROLE] working on [PROJECT_TYPE] using [TECH_STACK].

## Core Standards
- Language: [PRIMARY_LANGUAGE]
- Framework: [FRAMEWORK_NAME] 
- Style: [STYLE_REQUIREMENTS]
- Testing: [TEST_FRAMEWORK]

## Code Patterns

### [LANGUAGE_1]
- [RULE_1]
- [RULE_2]
- [RULE_3]

### [LANGUAGE_2] 
- [RULE_1]
- [RULE_2]
- [RULE_3]

## Error Handling
- [ERROR_PATTERN_1]
- [ERROR_PATTERN_2]

## Documentation
- [DOC_REQUIREMENT_1]
- [DOC_REQUIREMENT_2]
```

## Template B: Specialized File (Secondary)

```markdown
---
applyTo: "**/*.ts,**/*.tsx"
description: "[LANGUAGE] standards"
---

# [LANGUAGE] Instructions

## Standards
- [SPECIFIC_RULE_1]
- [SPECIFIC_RULE_2]

## Code Examples
```[LANGUAGE]
// Good pattern
[EXAMPLE_CODE]
```

## Anti-patterns
```[LANGUAGE]
// Avoid this
[ANTI_PATTERN_CODE]
```
```

## Template C: Cross-Reference Setup

```markdown
<!-- Main file references -->
- TypeScript: Apply [typescript.instructions.md](.github/instructions/typescript.instructions.md)
- Testing: Apply [testing.instructions.md](.github/instructions/testing.instructions.md)

<!-- Specialized file references -->
Follow [general guidelines](../copilot-instructions.md) for overall standards.
```

## File Structure Options

### Option 1: Single File (Recommended)
```
.github/
└── copilot-instructions.md
```

### Option 2: Multi-File (If Single > 200 lines)
```
.github/
├── copilot-instructions.md
└── instructions/
    ├── [language].instructions.md
    ├── testing.instructions.md
    └── security.instructions.md
```

## Verification Commands

```bash
# Test file existence
ls -la .github/copilot-instructions.md

# Test specialized files
ls -la .github/instructions/*.instructions.md

# Test pattern matching
find . -name "*.ts" | head -3
find . -name "test_*" | head -3
```

## Implementation Steps

1. **Enable Setting**
   ```json
   {"github.copilot.chat.codeGeneration.useInstructionFiles": true}
   ```

2. **Create Main File**
   ```bash
   mkdir -p .github
   touch .github/copilot-instructions.md
   ```

3. **Add Content** (Use Template A)

4. **Test Integration**
   - Ask Copilot to generate code
   - Check References list shows instruction file
   - Verify generated code follows instructions

5. **Optional: Add Specialized Files**
   ```bash
   mkdir -p .github/instructions
   touch .github/instructions/[name].instructions.md
   ```

## Common Patterns

### Web Development
```markdown
# Web Development Instructions
- Frontend: React with TypeScript, Tailwind CSS
- Backend: Node.js with Express, TypeScript
- Database: PostgreSQL with Prisma ORM
- Testing: Jest for unit tests, Cypress for E2E
- Style: ESLint + Prettier, strict TypeScript
```

### Python Projects  
```markdown
# Python Project Instructions
- Python 3.11+, use type hints everywhere
- FastAPI for web APIs, Pydantic for validation
- SQLAlchemy for database, Alembic for migrations
- pytest for testing, black for formatting
- Follow PEP 8, include docstrings
```

### Full-Stack Applications
```markdown
# Full-Stack Application Instructions
- Frontend: Next.js 14+ with TypeScript, Tailwind
- Backend: Python FastAPI or Node.js Express
- Database: PostgreSQL, Redis for caching
- Auth: NextAuth.js or FastAPI-Users
- Deployment: Docker containers, GitHub Actions
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Instructions ignored | Check setting enabled, restart VS Code |
| File not found | Verify `.github/copilot-instructions.md` path |
| applyTo not working | Use single file approach |
| Multiple conflicting rules | Consolidate to main file |

## Integration Prompts

```
Apply the coding standards from .github/copilot-instructions.md
Follow our project's instruction file requirements
Generate code matching our .github/copilot-instructions.md patterns
Check if this follows our project instruction file standards
```

## Validation Checklist

- [ ] Setting `github.copilot.chat.codeGeneration.useInstructionFiles` enabled
- [ ] File `.github/copilot-instructions.md` exists and has content
- [ ] Copilot References shows instruction file when generating code
- [ ] Generated code follows specified patterns
- [ ] Links between instruction files work (if using multiple files)

## File Size Guidelines

- Main file: 50-200 lines optimal
- Specialized files: 20-100 lines each  
- Total files: Maximum 5 (1 main + 4 specialized)
- If exceeding limits: consolidate or simplify rules
