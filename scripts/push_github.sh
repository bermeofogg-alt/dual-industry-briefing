#!/bin/zsh
# 每日晨报 → GitHub 推送
# 用法: ./scripts/push_github.sh "commit 说明（可选）" [日期 YYYY-MM-DD]
# 认证: GitHub CLI（gh auth login 已完成，credential helper 已配置），不再依赖手工 PAT
# 网络: GitHub 直连不稳定，走本机 Clash 代理 127.0.0.1:7890
# 并发: 自带文件锁（.state/git.lock，TTL 600s）；推送前先 rebase，避免并发导致 non-fast-forward

set -e
PROJ_DIR="/Users/jiangjuji/WorkBuddy/dual-industry-briefing"
REMOTE_REPO="https://github.com/bermeofogg-alt/dual-industry-briefing.git"
PROXY="http://127.0.0.1:7890"
export PATH="$HOME/.local/bin:$PATH"

cd "$PROJ_DIR"
mkdir -p .state

# 0) 文件锁：同一时刻只允许一个推送流程
GIT_LOCK=".state/git.lock"
GIT_LOCK_TTL=600
if ! mkdir "$GIT_LOCK" 2>/dev/null; then
  LOCK_MTIME=$(stat -f %m "$GIT_LOCK" 2>/dev/null || date +%s)
  AGE=$(( $(date +%s) - LOCK_MTIME ))
  if [[ $AGE -gt $GIT_LOCK_TTL ]]; then
    echo "⚠️  回收僵尸推送锁（已 ${AGE}s）"
    rm -rf "$GIT_LOCK"
    mkdir "$GIT_LOCK"
  else
    echo "❌ 另一个推送流程正在执行（锁已持有 ${AGE}s），本次跳过，避免并发写入"
    exit 1
  fi
fi
trap 'rm -rf "$PROJ_DIR/$GIT_LOCK"' EXIT INT TERM

# 1) 初始化 / 远程配置
[[ -d .git ]] || git init -b main
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_REPO"
else
  git remote add origin "$REMOTE_REPO"
fi

# 2) 代理、身份、凭证 helper（由 gh 提供）
git config http.proxy "$PROXY"
git config https.proxy "$PROXY"
git config user.name  "bermeofogg-alt"
git config user.email "bermeofogg-alt@users.noreply.github.com"
gh auth setup-git >/dev/null 2>&1 || true

# 3) 渲染 + 暂存（数据、版式、产物一并入库）
DATE_STR="${2:-$(date +%Y-%m-%d)}"
if [[ -f "data/${DATE_STR}.json" ]]; then
  python3 build.py "$DATE_STR" >/dev/null
fi

git add data assets build.py README.md scripts .gitignore index.html legacy 2>/dev/null || true
# Wizshot 素材含人像/人声，只用于站点发布，绝不提交到公开仓库（防 git add -A 误加）
git reset -q -- wizshot-assets 2>/dev/null || true
MSG="${1:-chore: 晨报数据更新 $(date +%Y-%m-%d)}"
if git diff --cached --quiet; then
  echo "没有变更需要提交"
else
  git commit -m "$MSG" >/dev/null
fi

# 4) 先同步远端再推（并发执行时避免 non-fast-forward）
BRANCH=$(git rev-parse --abbrev-ref HEAD)
set +e
git -c core.hooksPath=/dev/null pull --rebase --autostash origin "$BRANCH" >/dev/null 2>&1
REBASE_RC=$?
[[ $REBASE_RC -ne 0 ]] && echo "⚠️  远端同步跳过（无更新或无跟踪分支）"

git push -u origin "$BRANCH" > /tmp/gh_push_out.txt 2>&1
PUSH_RC=$?
tail -2 /tmp/gh_push_out.txt

if [[ $PUSH_RC -ne 0 ]]; then
  echo "⚠️  首次推送失败，rebase 后重试一次"
  git pull --rebase --autostash origin "$BRANCH" >/dev/null 2>&1
  git push -u origin "$BRANCH" > /tmp/gh_push_out.txt 2>&1
  PUSH_RC=$?
  tail -2 /tmp/gh_push_out.txt
fi
set -e

if [[ $PUSH_RC -eq 0 ]]; then
  echo "✅ 已推送到 $REMOTE_REPO"
else
  echo "❌ 推送失败，详情见上方输出（不自动重试第二次）"
  exit 1
fi
