#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度千帆 ERNIE-Wizshot-ME（文心一镜微表情大模型）客户端
=========================================================
让静态人像开口说话，生成 4–15 秒 1080p 真人口播视频。

注意：这是【异步视频生成模型】，不是 chat/completions 对话模型，
      不要写进 WorkBuddy 的自定义模型列表（models.json），会被当聊天模型调用而失败。

接口：
  创建任务  POST https://qianfan.baidubce.com/v2/mm/ernie/ernie-wizshot-me
  查询任务  GET  https://qianfan.baidubce.com/v2/mm/ernie/tasks?task_id=xxx
鉴权：Authorization: Bearer <API Key>（复用 ernie.json 里的 key）
计费：0.7 元/秒，10 秒约 ¥7；并发限制 1，队列 1。

⚠️ 素材必须是【公网可访问的 URL】，不接受本地路径或 base64：
  - avatar_url / shot_image : JPEG/PNG/WEBP 图片 URL
  - mid                     : 含人声的 wav，时长 10–60s
  千帆的「文件上传」接口返回的是 file_id（供对话 file_ids 用），不能当 URL 用。

命令行：
  python3 scripts/wizshot.py --check                       # 零成本自检（不生成视频）
  python3 scripts/wizshot.py --payload job.json --output ~/Desktop/ad.mp4
  python3 scripts/wizshot.py --task-id 67c999... --output ~/Desktop/ad.mp4
  python3 scripts/wizshot.py --task-id 67c999... --status  # 只查状态

payload JSON 结构见 README「Wizshot-ME」章节，或 --example 打印模板。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://qianfan.baidubce.com"
CREATE_PATH = "/v2/mm/ernie/ernie-wizshot-me"
QUERY_PATH = "/v2/mm/ernie/tasks"
MODEL = "ernie-wizshot-me"
PRICE_PER_SEC = 0.7
CONFIG_PATH = os.path.expanduser("~/.config/dual-industry-briefing/ernie.json")

EXAMPLE = {
    "model": MODEL,
    "personas": {
        "主播": {
            "mid": "https://<公网可访问>/voice-sample.wav",
            "avatar_url": "https://<公网可访问>/portrait.png",
            "name": "主播",
            "identity": "家纺品牌带货主播",
            "temperament": "亲切松弛、真诚自然",
        }
    },
    "fragments": [
        {
            "shots": [
                {
                    "camera_settings": {
                        "camera_movement": "正面机位，平视中近景",
                        "shot_image": "https://<公网可访问>/portrait.png",
                    },
                    "characters": ["主播"],
                    "segments": [
                        {
                            "character_speaker": "主播",
                            "production_elements": {
                                "dialog": "这套被子一摸就不想撒手，软得像陷进云里，今天下单还送同款收纳袋。",
                                "emotion": "开场惊喜亲近，讲到触感时放松笃定，收尾轻快带笑意",
                                "performance": "开场眼睛微微睁大、身体前倾；讲到「软」时手掌轻拍怀里的枕头；收尾点头看向镜头",
                                "voice_settings": "带货快语速，开头稍提亮，「云里」放慢半拍，尾音轻快上扬",
                            },
                        }
                    ],
                }
            ]
        }
    ],
}


# ---------------------------------------------------------------- 基础
def load_key():
    key = os.environ.get("QIANFAN_API_KEY")
    if not key and os.path.exists(CONFIG_PATH):
        try:
            key = json.load(open(CONFIG_PATH, encoding="utf-8")).get("api_key", "")
        except Exception as e:
            print(f"[warn] 读取配置失败：{e}", file=sys.stderr)
    if not key:
        raise RuntimeError(
            f"未找到 API Key。请在 {CONFIG_PATH} 填入 api_key，或 export QIANFAN_API_KEY=..."
        )
    return key.strip()


def _opener():
    # 国内域名强制直连，绕开系统代理
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _request(method, url, body=None, timeout=60):
    key = load_key()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _opener().open(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        raise RuntimeError(_friendly(e.code, raw)) from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络不可达：{e.reason}") from None


def _friendly(code, raw):
    biz = ""
    try:
        biz = (json.loads(raw).get("error") or {}).get("code", "") or ""
    except Exception:
        pass
    hints = {
        "invalid_video_generation_argument": "参数不合法（这是自检期望的结果，说明鉴权与路径都通了）",
        "video_generation_concurrency_exceeded": "并发已满：该模型并发限制 1、队列 1，等上个任务跑完再提交",
        "video_generation_prompt_unsafe": "输入图或文案被安全策略拦截：换素材/措辞",
        "video_generation_output_unsafe": "生成结果被安全策略拦截：换素材/措辞",
        "video_generation_internal_error": "服务端内部错误，稍后重试",
        "video_generation_risk_system_error": "风控系统异常，稍后重试",
    }
    code_hint = {400: "请求参数有误", 401: "API Key 无效或未开通该模型", 403: "无权限或触发安全策略",
                 404: "路径不存在", 429: "限流", 500: "服务端异常"}.get(code, "未预期状态码")
    return f"HTTP {code}{'（' + biz + '）' if biz else ''} — {hints.get(biz) or code_hint}\n返回体：{raw[:600]}"


# ---------------------------------------------------------------- 接口
def create(payload):
    """创建视频生成任务，返回 (task_id, 原始响应)。"""
    payload = dict(payload)
    payload.setdefault("model", MODEL)
    r = _request("POST", BASE + CREATE_PATH, payload)
    tid = r.get("task_id") or ""
    if not tid:
        raise RuntimeError(f"创建成功但未返回 task_id：{json.dumps(r, ensure_ascii=False)[:400]}")
    return tid, r


def query(task_id):
    """查询任务状态，返回完整响应。"""
    url = BASE + QUERY_PATH + "?" + urllib.parse.urlencode({"task_id": task_id})
    return _request("GET", url, timeout=30)


def wait(task_id, interval=10, timeout=900, verbose=True):
    """轮询直到 succeeded / failed，返回最终响应。"""
    start = time.time()
    last = ""
    while time.time() - start < timeout:
        r = query(task_id)
        status = r.get("status", "unknown")
        if status != last and verbose:
            print(f"  [{time.strftime('%H:%M:%S')}] status={status}", flush=True)
            last = status
        if status in ("succeeded", "failed"):
            return r
        time.sleep(interval)
    raise TimeoutError(f"等待超时（{timeout}s），可用 --task-id {task_id} --status 继续查询")


def find_video_urls(obj, found=None):
    """递归从 content 里找视频 URL（不同版本字段名不一致，做容错）。"""
    if found is None:
        found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("http") and re.search(
                r"\.(mp4|mov|webm)(\?|$)", v, re.I
            ):
                found.append((k, v))
            else:
                find_video_urls(v, found)
    elif isinstance(obj, list):
        for v in obj:
            find_video_urls(v, found)
    return found


def download(url, out_path):
    out_path = os.path.expanduser(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _opener().open(req, timeout=180) as r, open(out_path, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return out_path


def check():
    """零成本自检：用非法参数确认鉴权/路径/模型权限都通，不产生视频费用。"""
    print(f"接口：{BASE + CREATE_PATH}")
    print(f"查询：{BASE + QUERY_PATH}")
    print(f"Key ：{load_key()[:12]}…（已配置）")
    try:
        _request("POST", BASE + CREATE_PATH, {"model": MODEL})
    except RuntimeError as e:
        msg = str(e)
        if "HTTP 400" in msg or "invalid_video_generation_argument" in msg:
            print("✅ 自检通过：鉴权有效、路径正确、模型已开通（返回 400 是预期的参数校验，未生成视频、未计费）")
            return 0
        if "HTTP 401" in msg or "HTTP 403" in msg or "HTTP 404" in msg:
            print(f"❌ 模型不可用：{msg}")
            return 2
        print(f"⚠️ 非预期返回：{msg}")
        return 3
    print("⚠️ 意外地创建成功了任务（正常应因缺 personas/fragments 报 400），请检查是否产生了计费")
    return 1


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="千帆 ERNIE-Wizshot-ME 视频生成客户端")
    ap.add_argument("--check", action="store_true", help="零成本自检")
    ap.add_argument("--example", action="store_true", help="打印 payload 模板到 stdout")
    ap.add_argument("--payload", help="payload JSON 文件路径，创建任务并自动等待+下载")
    ap.add_argument("--task-id", help="查询/等待已有任务")
    ap.add_argument("--status", action="store_true", help="配合 --task-id，只查一次状态")
    ap.add_argument("--output", help="视频保存路径（.mp4）")
    ap.add_argument("--interval", type=int, default=10, help="轮询间隔秒，默认 10")
    ap.add_argument("--timeout", type=int, default=900, help="最长等待秒，默认 900")
    ap.add_argument("--yes", action="store_true", help="跳过费用确认")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=2))
        return 0
    if args.check:
        return check()

    if args.payload:
        with open(args.payload, "r", encoding="utf-8") as f:
            payload = json.load(f)
        dialogs = [
            s.get("production_elements", {}).get("dialog", "")
            for fr in payload.get("fragments", [])
            for sh in fr.get("shots", [])
            for s in sh.get("segments", [])
        ]
        chars = sum(len(d) for d in dialogs)
        est = max(4, min(15, round(chars / 4.5)))
        print(f"台词 {chars} 字，估算时长约 {est}s，费用约 ¥{est * PRICE_PER_SEC:.1f}（0.7 元/秒）")
        if not args.yes:
            print("加 --yes 确认提交；或 Ctrl+C 取消。")
            if sys.stdin.isatty():
                input("回车继续…")
        tid, raw = create(payload)
        print(f"✅ 任务已创建 task_id={tid}  request_id={raw.get('id', '')}")
        args.task_id = tid
        args.status = False

    if not args.task_id:
        ap.print_help()
        return 2

    if args.status:
        print(json.dumps(query(args.task_id), ensure_ascii=False, indent=2))
        return 0

    r = wait(args.task_id, interval=args.interval, timeout=args.timeout)
    print(json.dumps(r, ensure_ascii=False, indent=2)[:1200])
    if r.get("status") != "succeeded":
        print(f"❌ 任务未成功：status={r.get('status')}", file=sys.stderr)
        return 1

    urls = find_video_urls(r.get("content") or r)
    if not urls:
        print("⚠️ 任务成功但没找到 .mp4 链接，请从上面的原始响应里手动取 URL", file=sys.stderr)
        return 1
    out = args.output or os.path.expanduser(f"~/Desktop/wizshot-{args.task_id[:8]}.mp4")
    print(f"⬇️  下载 {urls[0][1]} → {out}")
    download(urls[0][1], out)
    size = os.path.getsize(out)
    print(f"✅ 已保存：{out}  ({size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        sys.exit(130)
    except (RuntimeError, TimeoutError, OSError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
