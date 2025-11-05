param(
  [string]$RemoteUrl = "",
  [string]$CommitMessage = "Initial commit"
)

# ...existing code...

Write-Host "Running git push helper..."

# initialize repo if missing
if (-not (Test-Path .git)) {
  Write-Host "No git repository found — initializing..."
  git init
}

# stage and commit
git add -A
$commitOutput = git commit -m $CommitMessage 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "Commit step: $commitOutput"
  Write-Host "Nothing to commit or commit failed; continuing."
}

# set remote if provided
if ($RemoteUrl -ne "") {
  Write-Host "Setting remote origin -> $RemoteUrl"
  git remote remove origin 2>$null
  git remote add origin $RemoteUrl
}

# ensure branch exists and is named main
$branch = (git rev-parse --abbrev-ref HEAD) -replace "`n",""
if ($branch -eq "HEAD" -or $branch -eq "") {
  git branch -M main
  $branch = "main"
  Write-Host "Created/renamed branch to 'main'"
}

# push
Write-Host "Pushing branch '$branch' to origin..."
git push -u origin $branch
if ($LASTEXITCODE -eq 0) {
  Write-Host "Push successful."
} else {
  Write-Host "Push failed. Check remote URL and authentication."
}

