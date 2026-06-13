# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-13

### Added

**Git Branch Management**
- Branch listing with `easy git branch list` (local and remote)
- Branch copying with `easy git branch copy <old> <new>`
- Branch deletion with safe (`-d`) and force (`-D`) modes
- Branch renaming with `easy git branch rename <old> <new>`
- Branch status queries: `merged`, `unmerged`
- Fast branch switching: `easy git switch <branch>`
- Create and switch in one command: `easy git switch new <branch>`
- Branch-specific commit history with `easy git branch log <branch>`

**Git Merge & Rebase Operations**
- Standard merge: `easy git merge <branch>`
- Merge with explicit commit: `easy git merge no-ff <branch>`
- Squash merge: `easy git merge squash <branch>`
- Rebase current branch: `easy git rebase <branch>`
- Interactive rebase: `easy git rebase interactive <branch>`
- Rebase recovery: `easy git rebase continue` and `easy git rebase abort`

**Git Pull & History Inspection**
- Pull variants: standard (`easy git pull`) and with rebase (`easy git pull rebase`)
- Commit history viewing:
  - Last 10 commits by default: `easy git log`
  - Last n commits: `easy git log past <count>`
  - Visual branch graph: `easy git log graph`
  - Commit diffs: `easy git log diff`
- Commit details: `easy git show <commit>`

**Git Change Inspection**
- Unstaged changes: `easy git diff`
- Staged changes: `easy git diff staged`
- Compare with branch: `easy git diff <branch>`

**Git Undo & Cleanup**
- File unstaging: `easy git reset <file>`
- Commit undo: `easy git revert <commit>` (non-destructive)
- Working tree restore: `easy git restore <file>`
- Untracked file cleanup: `easy git clean untracked`

**Test Coverage**
- 41 new test cases covering all git command variations
- All operations properly risk-classified (SAFE for read-only, MILD for writes)
- Comprehensive error handling with user-friendly messages

### Repository Improvements

- **LICENSE**: Added MIT license for open-source distribution
- **README**: Expanded with complete list of 45+ supported git command variations
- **Documentation**: Verified architecture documentation is complete
- **Testing**: Maintained 100% test pass rate (56 tests)

## [0.0.1] - Initial MVP

### Added

- Core fuzzy command resolution system
- Git MVP: init, status, commit, push, remote, repo
- Python runner command
- File open and find commands
- Documentation system
- Local history tracking
- Risk-based command execution control
