# Git Workflow With Protected `main`

This repository follows protected branch rules on `main`.

## Rules

- Never push directly to `main`.
- Create a feature branch for all changes.
- Open PRs to `main`.
- Merge only after CI is green.
- Use rebase merge only; do not use merge commits or squash for governed Lotus Gateway PRs.
- Delete the feature branch after merge.

## Daily Flow

```bash
git checkout main
git pull origin main
git checkout -b feat/<short-change-name>
make check
git add .
git commit -m "type: short summary"
git push -u origin feat/<short-change-name>
gh pr create --fill --base main --head feat/<short-change-name>
gh pr checks <PR_NUMBER> --watch
gh pr merge <PR_NUMBER> --rebase --delete-branch
git checkout main
git pull origin main
```

## Rebase Before Push

```bash
git fetch origin
git rebase origin/main
make check
git push --force-with-lease
```
