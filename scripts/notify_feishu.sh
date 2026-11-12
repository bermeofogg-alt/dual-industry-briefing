#!/bin/zsh
# 每日晨报 → 飞书群推送（自定义群机器人 webhook）
# 用法: ./scripts/notify_feishu.sh "标题" "正文（支持换行）" "链接URL（可选）"
# 凭证: ~/.config/dual-industry-briefing/feishu.webhook（webhook 地址，一行）
#       可选 ~/.config/dual-industry-briefing/feishu.secret（机器人开启「签名校验」时填密钥）
# 调试: FEISHU_WEBHOOK / FEISHU_SECRET 环境变量可临时覆盖（优先级高于配置文件）

set -e
CONF_DIR="$HOME/.config/dual-industry-briefing"
WEBHOOK_FILE="$CONF_DIR/feishu.webhook"
SECRET_FILE="$CONF_DIR/feishu.secret"

if [[ -n "$FEISHU_WEBHOOK" ]]; then
  WEBHOOK="$FEISHU_WEBHOOK"
elif [[ -f "$WEBHOOK_FILE" ]]; then
  WEBHOOK=$(tr -d '[:space:]' < "$WEBHOOK_FILE")
else
  echo "❌ 未找到 $WEBHOOK_FILE，且未设置 FEISHU_WEBHOOK"
  echo "   请把飞书群机器人的 webhook 地址存入该文件："
  echo "   mkdir -p $CONF_DIR && echo 'https://open.feishu.cn/open-apis/bot/v2/hook/xxxx' > $WEBHOOK_FILE"
  exit 1
fi

if [[ -n "$FEISHU_SECRET" ]]; then
  SECRET="$FEISHU_SECRET"
elif [[ -f "$SECRET_FILE" ]]; then
  SECRET=$(tr -d '[:space:]' < "$SECRET_FILE")
else
  SECRET=""
fi

TITLE="${1:-每日晨报}"
BODY="${2:-}"
URL="${3:-}"

LINK_LINE=""
if [[ -n "$URL" ]]; then
  LINK_LINE=$'\n'"────────────────"$'\n'"[点击查看完整晨报](${URL})"
fi

# 卡片：标题 + 正文 + 链接 + 落款时间
BODY_MD="${BODY}${LINK_LINE}"
STAMP=$(date "+%Y-%m-%d %H:%M")

PAYLOAD=$(jq -n \
  --arg title "$TITLE" \
  --arg body "$BODY_MD" \
  --arg stamp "$STAMP" \
  '{msg_type:"interactive", card:{config:{wide_screen_mode:true}, header:{template:"green", title:{tag:"plain_text", content:$title}}, elements:[
      {tag:"div", text:{tag:"lark_md", content:$body}},
      {tag:"hr"},
      {tag:"note", elements:[{tag:"plain_text", content:("家纺 & 零售每日晨报 · " + $stamp)}]}
    ]}}')

# 开启签名校验时，把 timestamp + sign 拼到 URL 上（飞书官方算法：key = "timestamp\nsecret"，消息体为空，HMAC-SHA256 后 base64）
if [[ -n "$SECRET" ]]; then
  TS=$(date +%s)
  SIGN=$(python3 -c "
import hmac, hashlib, base64, sys
ts, sec = sys.argv[1], sys.argv[2]
key = ('%s\n%s' % (ts, sec)).encode('utf-8')
print(base64.b64encode(hmac.new(key, b'', hashlib.sha256).digest()).decode())
" "$TS" "$SECRET")
  SEP="?"
  [[ "$WEBHOOK" == *"?"* ]] && SEP="&"
  WEBHOOK="${WEBHOOK}${SEP}timestamp=${TS}&sign=$(printf '%s' "$SIGN" | jq -sRr @uri)"
fi

HTTP_CODE=$(curl -s -o /tmp/feishu_resp.json -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  --max-time 20 \
  -d "$PAYLOAD" "$WEBHOOK")

RESP=$(cat /tmp/feishu_resp.json 2>/dev/null)
echo "HTTP $HTTP_CODE | $RESP"

# 飞书可能返回 {"code":0,...} 或 {"StatusCode":0,...}，带不带空格都有，统一用 jq 解析
CODE=$(printf '%s' "$RESP" | jq -r 'if type=="object" then (.code // .StatusCode // -1) else -1 end' 2>/dev/null || echo -1)

if [[ "$CODE" == "0" ]]; then
  echo "✅ 已推送到飞书"
else
  case "$RESP" in
    *19021*) echo "❌ 签名校验失败：feishu.secret 与机器人「签名校验」密钥不一致，或服务器时间偏差过大" ;;
    *19001*|*19002*|*19003*) echo "❌ webhook 地址无效或机器人已被移除，请重新复制地址" ;;
    *"Key Words Not Found"*) echo "❌ 机器人开启了「自定义关键词」，卡片需包含该关键词（建议设为「晨报」）" ;;
    *19024*|*"Ip Not Allowed"*) echo "❌ 机器人开启了 IP 白名单，需关闭或放行当前出口 IP" ;;
    *) echo "❌ 飞书返回异常（code=$CODE），请检查 webhook 地址与卡片格式" ;;
  esac
  exit 1
fi
