# Test-First Git Workflow

## Overview
This workflow ensures all code changes are thoroughly tested before being committed to the repository. Cline will automatically run tests, fix failing tests if needed, and only push code that passes all tests.

## Workflow Steps

### 1. After Making Changes or Adding Features
- Run complete test suite on entire codebase
- Wait for test results

### 2. If All Tests Pass
- Stage all changes: `git add .`
- Commit with descriptive message: `git commit -m "feat/fix: [description]"`
- Push to remote repository: `git push origin [branch-name]`

### 3. If Any Tests Fail
- **DO NOT COMMIT OR PUSH**
- Analyze failing test output
- Identify root cause of test failures
- Fix the failing tests by either:
  - Correcting the implementation code
  - Updating test expectations if they're outdated
  - Fixing test setup/teardown issues
- Re-run complete test suite
- Repeat until all tests pass
- Only then proceed to commit and push

## Test Commands
```bash
# Run all tests
npm test
# or
yarn test
# or
pytest
# or whatever test command is appropriate for the project
```

## Git Commands
```bash
# Stage changes
git add .

# Commit with message
git commit -m "descriptive commit message"

# Push to remote
git push origin main
```

## Important Notes
- **Never push failing tests**
- Always run the full test suite, not just affected tests
- Fix tests immediately when they fail
- Use descriptive commit messages
- Ensure working directory is clean before starting new features

## Success Criteria
✅ All tests pass  
✅ Code is committed with clear message  
✅ Changes are pushed to remote repository  
✅ Working directory is clean