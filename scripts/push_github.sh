#!/bin/zsh
# 每日晨报 → GitHub 推送
# 用法: ./scripts/push_github.sh "commit 说明（可选，默认取当日日期）"
# 凭证: ~/.config/dual-industry-briefing/github.token（GitHub PAT，需 repo 权限）
#       若不存在则回退到系统 git 凭证（gh 登录或钥匙串）

set -e
PROJ_DIR="/Users/jiangjuji/WorkBuddy/dual-industry-briefing"
TOKEN_FILE="$HOME/.config/dual-industry-briefing/github.token"
REMOTE_REPO="https://github.com/jiangjuji/dual-industry-briefing.git"
PROXY="http://127.0.0.1:7890"   # Clash Verge 本地代理，GitHub 需走代理

cd "$PROJ_DIR"

# 1) 认证：优先 PAT，回退系统凭证
if [[ -f "$TOKEN_FILE" ]]; then
  TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')
  AUTH_REMOTE="https://jiangjuji:${TOKEN}@github.com/jiangjuji/dual-industry-briefing.git"
else
  AUTH_REMOTE="$REMOTE_REPO"
fi

# 2) 初始化 / 远程配置
if [[ ! -d .git ]]; then
  git init -b main
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$AUTH_REMOTE"
else
  git remote set-url origin "$AUTH_REMOTE"
fi

# 3) 代理与身份
git config http.proxy "$PROXY"
git config https.proxy "$PROXY"
git config user.name  "jiangjuji"
git config user.email "jiangjuji@users.noreply.github.com"

# 4) 提交并推送（数据与版式，不含生成的 index.html）
git add data assets build.py README.md scripts .gitignore
MSG="${1:-chore: 晨报数据更新 $(date +%Y-%m-%d)}"
if git diff --cached --quiet; then
  echo "没有变更需要提交"
else
  git commit -m "$MSG"
fi

# 5) 推送（首次推送建立 upstream）
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if git ls-remote --heads "$REMOTE_REPO" "$BRANCH" | grep -q "$BRANCH"; then
  git push origin "$BRANCH"
else
  echo "远程仓库不存在或不可见 → 请先在 GitHub 上创建空仓库 dual-industry-briefing（私有/公开均可），或检查 token"
  git push -u origin "$BRANCH" || exit 1
fi
echo "✅ 已推送到 $REMOTE_REPO"
