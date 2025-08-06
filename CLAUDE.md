# Claude Development Guide

## GitHub CLI (gh) Commands Reference

### Installation
```bash
# Windows (using winget)
winget install --id GitHub.cli

# After installation, authenticate
gh auth login
```

### Common gh Commands

#### Authentication
```bash
# Login to GitHub
gh auth login

# Check authentication status
gh auth status

# Logout
gh auth logout
```

#### Repository Commands
```bash
# View repository info
gh repo view

# Clone a repository
gh repo clone owner/repo

# Create a new repository
gh repo create repo-name --public/--private

# Fork a repository
gh repo fork owner/repo
```

#### Issue Commands
```bash
# List issues
gh issue list
gh issue list --state closed
gh issue list --label bug
gh issue list --assignee @me

# View specific issue
gh issue view 123
gh issue view 123 --web  # Open in browser

# Create new issue
gh issue create --title "Issue title" --body "Issue description"
gh issue create --title "Bug: Something broken" --label bug --label priority-high

# Create issue with multi-line body
gh issue create --title "Feature: New component" --body "$(cat <<'EOF'
## Description
Detailed description here

## Tasks
- [ ] Task 1
- [ ] Task 2
EOF
)"

# Close/reopen issue
gh issue close 123
gh issue reopen 123

# Edit issue
gh issue edit 123 --title "New title"
gh issue edit 123 --add-label bug
gh issue edit 123 --remove-label wontfix
```

#### Pull Request Commands
```bash
# List pull requests
gh pr list
gh pr list --state merged
gh pr list --author @me

# View specific PR
gh pr view 123
gh pr view 123 --web

# Create pull request
gh pr create --title "Fix: Resolve issue #123" --body "Description"
gh pr create --title "Feature: Add new component" --body "$(cat <<'EOF'
## Description
What this PR does

## Changes
- Change 1
- Change 2

## Testing
How to test

Closes #123
EOF
)"

# Create PR with specific base branch
gh pr create --base main --head feature-branch

# Check PR status
gh pr status

# Review PR
gh pr review 123 --approve
gh pr review 123 --request-changes --body "Please fix X"
gh pr review 123 --comment --body "Looks good!"

# Merge PR
gh pr merge 123 --merge    # Create merge commit
gh pr merge 123 --squash   # Squash and merge
gh pr merge 123 --rebase   # Rebase and merge

# Close PR without merging
gh pr close 123
```

#### Workflow Commands
```bash
# List workflows
gh workflow list

# View workflow runs
gh run list
gh run view 123

# Watch workflow run
gh run watch 123

# Re-run failed workflow
gh run rerun 123
```

## GitHub Flow Workflow

### Overview
GitHub Flow is a lightweight, branch-based workflow that supports teams and projects where deployments are made regularly.

### The Flow

#### 1. Create a Branch
```bash
# Create and switch to new branch
git checkout -b feature/new-feature
# or
git checkout -b fix/issue-123-bug-description
```

**Branch Naming Conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

#### 2. Make Changes
```bash
# Make your changes
# Edit files...

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add user authentication feature

- Implement login/logout functionality
- Add session management
- Create user model
- Add authentication tests"
```

**Commit Message Format:**
```
<type>: <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

#### 3. Push to GitHub
```bash
# Push branch to remote
git push -u origin feature/new-feature
```

#### 4. Create Pull Request
```bash
# Using gh CLI
gh pr create --title "Feature: Add user authentication" --body "$(cat <<'EOF'
## Description
This PR adds user authentication to the application.

## Changes
- Added login/logout endpoints
- Implemented session management
- Created user model and migrations
- Added authentication middleware

## Testing
- Run `npm test` to execute auth tests
- Manual testing: Try logging in/out

## Screenshots
[If applicable]

Closes #45
EOF
)"
```

#### 5. Code Review
- Request reviews from team members
- Address feedback and comments
- Make additional commits if needed
- Ensure all checks pass

#### 6. Merge
```bash
# After approval, merge the PR
gh pr merge 123 --squash  # Recommended for clean history
```

#### 7. Clean Up
```bash
# Delete local branch
git branch -d feature/new-feature

# Delete remote branch (usually automatic after PR merge)
git push origin --delete feature/new-feature
```

## Working with Issues

### Issue-Driven Development
1. **Create Issue First**
   ```bash
   gh issue create --title "Add user authentication" --body "$(cat <<'EOF'
   ## Description
   We need user authentication for the app.
   
   ## Requirements
   - Login/logout functionality
   - Session management
   - Password hashing
   - Remember me option
   
   ## Acceptance Criteria
   - [ ] Users can register
   - [ ] Users can login
   - [ ] Sessions persist
   - [ ] Passwords are secure
   EOF
   )" --label feature --label priority-high
   ```

2. **Reference Issue in Branch Name**
   ```bash
   git checkout -b feature/issue-45-user-auth
   ```

3. **Reference Issue in Commits**
   ```bash
   git commit -m "Add login functionality for #45"
   ```

4. **Close Issue via PR**
   ```bash
   # In PR description, include:
   "Closes #45" or "Fixes #45"
   ```

### Issue Templates
Create `.github/ISSUE_TEMPLATE/` directory with templates:

**bug_report.md:**
```markdown
---
name: Bug report
about: Create a report to help us improve
title: 'Bug: '
labels: bug
assignees: ''
---

## Description
A clear description of the bug.

## To Reproduce
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

## Expected behavior
What should happen.

## Screenshots
If applicable.

## Environment
- OS: [e.g. Windows 11]
- Browser: [e.g. Chrome 91]
- Version: [e.g. 1.0.0]
```

## Best Practices

### 1. Atomic Commits
- Each commit should represent one logical change
- Commits should be able to be reverted independently

### 2. Branch Protection
- Protect main branch
- Require PR reviews
- Require status checks to pass

### 3. PR Size
- Keep PRs small and focused
- Large features should be split into multiple PRs

### 4. Documentation
- Update documentation with code changes
- Include examples in PR descriptions

### 5. Testing
- Write tests for new features
- Ensure all tests pass before merging

### 6. Communication
- Use issue and PR comments for discussions
- Tag relevant people with @username
- Use labels effectively

## Quick Reference

### Complete Workflow Example
```bash
# 1. Start from updated main
git checkout main
git pull origin main

# 2. Create issue
gh issue create --title "Fix: Resolve parsing error" --label bug

# 3. Create branch (assume issue #123 was created)
git checkout -b fix/issue-123-parsing-error

# 4. Make changes and commit
git add .
git commit -m "Fix parsing error in Google invoice parser

- Handle edge case for empty descriptions
- Add validation for amount fields
- Update tests

Fixes #123"

# 5. Push and create PR
git push -u origin fix/issue-123-parsing-error
gh pr create --title "Fix #123: Resolve parsing error" --body "Fixes the parsing error reported in #123"

# 6. After review and approval
gh pr merge 123 --squash

# 7. Clean up
git checkout main
git pull origin main
git branch -d fix/issue-123-parsing-error
```

## Useful Aliases

Add to your `.gitconfig` or shell profile:

```bash
# Git aliases
alias gs='git status'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph'
alias gco='git checkout'

# gh aliases
alias ghil='gh issue list'
alias ghic='gh issue create'
alias ghprl='gh pr list'
alias ghprc='gh pr create'
alias ghprm='gh pr merge'
```

## Resources
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Best Practices](https://docs.github.com/en/get-started/quickstart/github-flow)