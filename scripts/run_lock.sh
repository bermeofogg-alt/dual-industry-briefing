#!/bin/zsh
# 晨报执行锁 + 数据快照守卫
# 用途：防止同日多次触发（或并发执行）互相覆盖 data 文件、重复发布与重复推送。
#
# 用法：
#   ./scripts/run_lock.sh begin  <YYYY-MM-DD>   # 取锁 + 给现有 data 打快照 + 报告最近改写时间
#   ./scripts/run_lock.sh end    <YYYY-MM-DD>   # 校验 JSON + 记录指纹 + 释放锁
#   ./scripts/run_lock.sh status                # 查看当前锁状态
#   ./scripts/run_lock.sh release               # 强制释放（异常中断后手工清理）
#
# 退出码：0 = 拿到锁/正常；1 = 已被占用（本次应直接跳过，不要写数据、不要发布）；2 = 参数错误
#
# 锁实现：mkdir 原子性（跨进程安全），带 TTL 自动回收僵尸锁。

set -u
PROJ_DIR="/Users/jiangjuji/WorkBuddy/dual-industry-briefing"
STATE_DIR="$PROJ_DIR/.state"
LOCK_DIR="$STATE_DIR/run.lock"
META_FILE="$LOCK_DIR/meta"
TTL_SEC=2700          # 45 分钟：单轮最长执行时间，超时视为僵尸锁
RECENT_SEC=180        # 3 分钟内被改写过 → 视为「上一轮刚写完」

mkdir -p "$STATE_DIR"

now_epoch() { date +%s; }
iso_now()   { date "+%Y-%m-%d %H:%M:%S"; }

lock_started_epoch() {
  # 优先读 meta；meta 尚未写出（抢锁竞态窗口）时用锁目录 mtime 兜底，绝不返回 0
  if [[ -f "$META_FILE" ]]; then
    local v
    v=$(awk -F= '/^start=/{print $2}' "$META_FILE" < /dev/null 2>/dev/null)
    if [[ -n "$v" && "$v" != "0" ]]; then
      echo "$v"
      return
    fi
  fi
  stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0
}

lock_at() {
  [[ -f "$META_FILE" ]] || { echo "-"; return; }
  awk -F= '/^at=/{print $2}' "$META_FILE" < /dev/null 2>/dev/null || echo "-"
}

lock_pid() {
  [[ -f "$META_FILE" ]] || { echo "?"; return; }
  awk -F= '/^pid=/{print $2}' "$META_FILE" < /dev/null 2>/dev/null || echo "?"
}

do_acquire() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    {
      echo "start=$(now_epoch)"
      echo "pid=$$"
      echo "at=$(iso_now)"
    } > "$META_FILE"
    echo "ACQUIRED pid=$$ at=$(iso_now)"
    return 0
  fi

  # 锁已存在：先给持锁者一点时间写完 meta（抢锁竞态窗口），再判断是否僵尸
  sleep 0.3
  local started age pid
  started=$(lock_started_epoch)
  pid=$(lock_pid)
  age=$(( $(now_epoch) - ${started:-0} ))
  if [[ $age -gt $TTL_SEC ]]; then
    echo "STALE_LOCK 回收僵尸锁（pid=$pid，已 ${age}s 未释放）"
    rm -rf "$LOCK_DIR"
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      { echo "start=$(now_epoch)"; echo "pid=$$"; echo "at=$(iso_now)"; } > "$META_FILE"
      echo "ACQUIRED pid=$$ at=$(iso_now)"
      return 0
    fi
  fi
  echo "LOCKED 已有执行在跑：pid=$pid，开始于 $(lock_at)，已 ${age}s"
  return 1
}

cmd="${1:-status}"
DATE_STR="${2:-$(date +%Y-%m-%d)}"

case "$cmd" in
  begin)
    do_acquire || exit 1

    DATA_FILE="$PROJ_DIR/data/${DATE_STR}.json"
    if [[ -f "$DATA_FILE" ]]; then
      STAMP=$(date +%H%M%S)
      cp "$DATA_FILE" "$STATE_DIR/${DATE_STR}.${STAMP}.bak"
      MTIME=$(stat -f %m "$DATA_FILE")
      FILE_AGE=$(( $(now_epoch) - MTIME ))
      echo "DATA_EXISTS 已有 data/${DATE_STR}.json，快照 → .state/${DATE_STR}.${STAMP}.bak（文件 ${FILE_AGE}s 前被改写）"
      if [[ $FILE_AGE -le $RECENT_SEC ]]; then
        echo "DATA_RECENT 上一轮 ${FILE_AGE}s 前刚写过：本次只允许增量替换，禁止整体重建"
      fi
    else
      echo "DATA_NEW 无 data/${DATE_STR}.json，本轮为首次写入"
    fi
    ;;

  end)
    DATA_FILE="$PROJ_DIR/data/${DATE_STR}.json"
    if [[ -f "$DATA_FILE" ]]; then
      if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$DATA_FILE" 2>/dev/null; then
        SHA=$(shasum -a 256 "$DATA_FILE" | awk '{print $1}')
        COUNTS=$(python3 - "$DATA_FILE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
h = sum(len(s['items']) for s in d['modules']['home']['sections'])
r = sum(len(s['items']) for s in d['modules']['retail']['sections'])
print(f"home={h} retail={r} quotes={len(d['quotes'])}")
PY
)
        echo "$(iso_now)  sha256=$SHA  $COUNTS" >> "$STATE_DIR/${DATE_STR}.history"
        echo "VALIDATED data/${DATE_STR}.json  $COUNTS  sha256=${SHA:0:12}"
      else
        echo "INVALID data/${DATE_STR}.json 不是合法 JSON，未记录指纹（请修复后再发布）"
      fi
    else
      echo "NO_DATA data/${DATE_STR}.json 不存在，跳过校验"
    fi
    rm -rf "$LOCK_DIR"
    echo "RELEASED 锁已释放"
    ;;

  release)
    rm -rf "$LOCK_DIR"
    echo "RELEASED 强制释放完成"
    ;;

  status)
    if [[ -d "$LOCK_DIR" ]]; then
      started=$(lock_started_epoch)
      age=$(( $(now_epoch) - ${started:-0} ))
      echo "LOCKED pid=$(lock_pid) at=$(lock_at) 已 ${age}s（TTL ${TTL_SEC}s）"
    else
      echo "FREE 当前无锁"
    fi
    ;;

  *)
    echo "用法: $0 begin|end|status|release [YYYY-MM-DD]"
    exit 2
    ;;
esac
