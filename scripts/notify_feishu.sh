#!/bin/zsh
# 每日晨报 → 飞书群推送（自定义群机器人 webhook）
# 用法: ./scripts/notify_feishu.sh "标题" "正文（支持换行）" "链接URL（可选）"
# 凭证: ~/.config/dual-industry-briefing/feishu.webhook（webhook 地址，一行）

set -e
WEBHOOK_FILE="$HOME/.config/dual-industry-briefing/feishu.webhook"

if [[ ! -f "$WEBHOOK_FILE" ]]; then
  echo "❌ 未找到 $WEBHOOK_FILE"
  echo "   请把飞书群机器人的 webhook 地址存入该文件："
  echo "   mkdir -p ~/.config/dual-industry-briefing && echo 'https://open.feishu.cn/open-apis/bot/v2/hook/xxxx' > $WEBHOOK_FILE"
  exit 1
fi

WEBHOOK=$(cat "$WEBHOOK_FILE" | tr -d '[:space:]')
TITLE="${1:-每日晨报}"
BODY="${2:-}"
URL="${3:-}"

LINK_LINE=""
if [[ -n "$URL" ]]; then
  LINK_LINE="[点击查看完整晨报](${URL})"
fi

PAYLOAD=$(jq -n \
  --arg title "$TITLE" \
  --arg body "$BODY" \
  --arg link "$LINK_LINE" \
  '{msg_type:"interactive", card:{config:{wide_screen_mode:true}, elements:[
      {tag:"div", text:{tag:"lark_md", content:("**" + $title + "**\n" + $body + "\n" + $link)}}
    ]}}')

HTTP_CODE=$(curl -s -o /tmp/feishu_resp.json -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" "$WEBHOOK")

RESP=$(cat /tmp/feishu_resp.json 2>/dev/null)
echo "HTTP $HTTP_CODE | $RESP"
if [[ "$RESP" == *'"code":0'* || "$RESP" == *'"StatusCode":0'* ]]; then
  echo "✅ 已推送到飞书"
else
  echo "❌ 飞书返回异常，请检查 webhook 地址与卡片格式"
  exit 1
fi
