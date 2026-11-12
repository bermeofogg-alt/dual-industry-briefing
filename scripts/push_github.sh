#!/bin/zsh
# 每日晨报 → GitHub 推送
# 用法: ./scripts/push_github.sh "commit 说明（可选）" [日期 YYYY-MM-DD]
# 认证: GitHub CLI（gh auth login 已完成，credential helper 已配置），不再依赖手工 PAT
# 网络: GitHub 直连不稳定，走本机 Clash 代理 127.0.0.1:7890

set -e
PROJ_DIR="/Users/jiangjuji/WorkBuddy/dual-industry-briefing"
REMOTE_REPO="https://github.com/bermeofogg-alt/dual-industry-briefing.git"
PROXY="http://127.0.0.1:7890"
export PATH="$HOME/.local/bin:$PATH"

cd "$PROJ_DIR"

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
MSG="${1:-chore: 晨报数据更新 $(date +%Y-%m-%d)}"
if git diff --cached --quiet; then
  echo "没有变更需要提交"
else
  git commit -m "$MSG" >/dev/null
fi

# 4) 推送
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$BRANCH" 2>&1 | tail -2
echo "✅ 已推送到 $REMOTE_REPO"
