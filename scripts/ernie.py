#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度千帆 ERNIE 客户端（零依赖，仅用标准库）
===========================================
端点：POST https://qianfan.baidubce.com/v2/chat/completions
模型：ernie-5.5-flash-preview（1M 上下文 / RPM 300 / TPM 3,000,000）

鉴权：Authorization: Bearer <API Key>
  API Key 存放顺序（前者优先）：
    1) 环境变量 QIANFAN_API_KEY
    2) ~/.config/dual-industry-briefing/ernie.json 的 api_key 字段

命令行用法：
  python3 scripts/ernie.py "你好，用一句话自我介绍"
  python3 scripts/ernie.py --system "你是家纺行业分析师" "总结这条新闻：..."
  python3 scripts/ernie.py --stream "写一段 100 字的晨报导语"
  python3 scripts/ernie.py --json "输出 JSON：{name, price}"
  python3 scripts/ernie.py --file prompt.txt --usage
  python3 scripts/ernie.py --check          # 连通性 + 密钥自检

作为模块调用：
  from ernie import chat
  r = chat([{"role": "user", "content": "你好"}])
  print(r["content"], r["usage"])
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://qianfan.baidubce.com/v2/chat/completions"
DEFAULT_MODEL = "ernie-5.5-flash-preview"
CONFIG_PATH = os.path.expanduser("~/.config/dual-industry-briefing/ernie.json")

CONFIG_TEMPLATE = {
    "api_key": "",
    "model": DEFAULT_MODEL,
    "base_url": "https://qianfan.baidubce.com/v2",
    "endpoint": ENDPOINT,
    "proxy": "",
    "timeout": 120,
    # 该模型是思考型，思考 token 计入输出计费；默认关闭，需要深度推理时用 --think
    "thinking": "disabled",
    "default_headers": {"appid": ""},
}

# 千帆价格（元 / 百万 token）——仅用于本地粗算，实际以控制台账单为准
PRICE = {
    "peak": {"in": 2.0, "out": 8.0},    # 08:00-22:00
    "off": {"in": 1.0, "out": 4.0},     # 22:00-08:00
}


# ---------------------------------------------------------------- 配置
def load_config(create_if_missing=True):
    cfg = dict(CONFIG_TEMPLATE)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f) or {})
        except Exception as e:
            print(f"[warn] 读取配置失败 {CONFIG_PATH}: {e}", file=sys.stderr)
    elif create_if_missing:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_TEMPLATE, f, ensure_ascii=False, indent=2)
        os.chmod(CONFIG_PATH, 0o600)
        print(f"[info] 已生成配置模板：{CONFIG_PATH}（请填入 api_key）", file=sys.stderr)
    cfg["api_key"] = os.environ.get("QIANFAN_API_KEY") or cfg.get("api_key") or ""
    return cfg


def save_api_key(key, cfg=None):
    """把 API Key 写入配置文件（权限 600）。"""
    cfg = cfg or load_config()
    cfg["api_key"] = key.strip()
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.chmod(CONFIG_PATH, 0o600)
    return CONFIG_PATH


# ---------------------------------------------------------------- 请求
def _opener(cfg):
    """proxy 为空时强制直连（忽略系统/环境变量代理），避免国内域名被代理拖慢。"""
    proxy = (cfg.get("proxy") or "").strip()
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _headers(cfg):
    if not cfg.get("api_key"):
        raise RuntimeError(
            "未找到 API Key。请任选其一：\n"
            f"  a) export QIANFAN_API_KEY='bce-v3/ALTAK-.../...'\n"
            f"  b) 在 {CONFIG_PATH} 的 api_key 字段填入\n"
            "  在千帆控制台「快速接入」页可创建通用 API Key。"
        )
    h = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key'].strip()}",
    }
    appid = (cfg.get("default_headers") or {}).get("appid", "").strip()
    if appid:
        h["appid"] = appid
    return h


def _payload(messages, cfg, model=None, stream=False, **kw):
    body = {
        "model": model or cfg.get("model") or DEFAULT_MODEL,
        "messages": messages,
        "stream": stream,
    }
    for k in ("temperature", "top_p", "max_tokens", "stop", "frequency_penalty",
              "presence_penalty", "response_format", "tools", "tool_choice",
              "reasoning_effort", "thinking"):
        if kw.get(k) is not None:
            body[k] = kw[k]
    # extra_body 里的字段直接平铺到请求体顶层（千帆特有参数走这里）
    extra = kw.get("extra_body") or {}
    for k, v in extra.items():
        body[k] = v
    # 默认按配置决定是否开启思考；调用方显式给 thinking 时以其为准
    if "thinking" not in body and cfg.get("thinking"):
        body["thinking"] = {"type": "enabled" if cfg["thinking"] == "enabled" else "disabled"}
    return body


def chat(messages, model=None, cfg=None, **kw):
    """非流式对话。返回 {content, reasoning, usage, raw, model}。"""
    cfg = cfg or load_config()
    stream_on = bool(kw.pop("stream", False))
    if stream_on:
        return "".join(stream_chat(messages, model=model, cfg=cfg, **kw))

    req = urllib.request.Request(
        cfg.get("endpoint") or ENDPOINT,
        data=json.dumps(_payload(messages, cfg, model, False, **kw)).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    try:
        with _opener(cfg).open(req, timeout=cfg.get("timeout", 120)) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(_friendly_error(e.code, body)) from None
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"网络不可达：{e.reason}\n"
            "  若本机启用了代理，可把配置里的 proxy 留空（默认直连），"
            "或设为 http://127.0.0.1:7890 再试。"
        ) from None

    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    content = msg.get("content") or ""
    usage = data.get("usage") or {}
    warning = None
    if not content and (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) > 0:
        warning = "正文为空：思考占满了 max_tokens 预算，请加大 --max-tokens 或去掉 --think。"
    # 该模型偶尔会忽略 thinking:disabled，把 max_tokens 全花在推理上导致正文为空。
    # 遇到这种情况自动放大预算重试一次，对调用方透明。
    if warning and not kw.pop("_retried", False):
        cap = kw.get("max_tokens") or 512
        if cap < 4096:
            retry_kw = {k: v for k, v in kw.items() if k != "max_tokens"}
            retry_kw["max_tokens"] = max(cap * 4, 512)
            retry_kw["_retried"] = True
            return chat(messages, model=model, cfg=cfg, **retry_kw)

    return {
        "content": content,
        "reasoning": msg.get("reasoning_content") or "",
        "usage": usage,
        "model": data.get("model") or (model or DEFAULT_MODEL),
        "warning": warning,
        "raw": data,
    }


def stream_chat(messages, model=None, cfg=None, **kw):
    """流式对话，逐段 yield 文本增量。"""
    cfg = cfg or load_config()
    req = urllib.request.Request(
        cfg.get("endpoint") or ENDPOINT,
        data=json.dumps(_payload(messages, cfg, model, True, **kw)).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    try:
        resp = _opener(cfg).open(req, timeout=cfg.get("timeout", 120))
    except urllib.error.HTTPError as e:
        raise RuntimeError(_friendly_error(e.code, e.read().decode("utf-8", "replace"))) from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络不可达：{e.reason}") from None

    with resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for ch in obj.get("choices") or []:
                piece = (ch.get("delta") or {}).get("content")
                if piece:
                    yield piece


def _friendly_error(code, body):
    # 先看千帆返回的 error.code，能给出比状态码更准的判断
    biz_code = ""
    try:
        biz_code = (json.loads(body).get("error") or {}).get("code", "") or ""
    except Exception:
        pass

    biz_hint = {
        "invalid_iam_token": "Bearer Token 本身无效（不是格式问题）：Key 拼错、已删除，或复制时带了引号/空格。",
        "iam_permission_denied": "Key 有效但无该模型权限：到千帆控制台给这个 Key 绑定 ernie-5.5-flash-preview。",
        "invalid_api_key": "API Key 不被识别，请确认是「通用 API Key」而非 Access Key。",
        "model_not_found": "模型未开通或 model 名不符：应为 ernie-5.5-flash-preview。",
        "quota_exceeded": "额度用尽：需在控制台续费或更换 Key。",
        "rate_limit_exceeded": "触发限流：默认 RPM 300 / TPM 3,000,000，请退避重试。",
        "invalid_request_error": "请求体格式有误，检查 messages 结构。",
    }.get(biz_code)

    code_hint = {
        400: "请求参数有误（常见：model 名写错、messages 为空、max_tokens 超限）",
        401: "鉴权失败：API Key 无效、已删除或未开通该模型。请到千帆控制台「快速接入」重新创建。",
        403: "无权限：该 API Key 未绑定此模型，或账号未实名/欠费。",
        404: "路径不存在：确认 base_url 为 https://qianfan.baidubce.com/v2 且 model 存在。",
        429: "限流或额度用尽：ernie-5.5-flash-preview 默认 RPM 300 / TPM 3,000,000，请退避重试。",
        500: "服务端异常，稍后重试。",
        503: "模型繁忙或维护中，稍后重试。",
    }.get(code, "未预期状态码")

    hint = f"{code_hint}｜{biz_hint}" if biz_hint else code_hint
    tag = f"（{biz_code}）" if biz_code else ""
    return f"HTTP {code}{tag} — {hint}\n返回体：{body[:600]}"


def cost_estimate(usage, hour=None):
    """按 token 粗算费用（元）。hour 默认取当前小时，用于区分忙/闲时。"""
    import datetime
    h = datetime.datetime.now().hour if hour is None else hour
    tier = PRICE["off"] if (h >= 22 or h < 8) else PRICE["peak"]
    pin = usage.get("prompt_tokens", 0) / 1_000_000 * tier["in"]
    pout = usage.get("completion_tokens", 0) / 1_000_000 * tier["out"]
    return {"prompt_yuan": round(pin, 6), "completion_yuan": round(pout, 6),
            "total_yuan": round(pin + pout, 6), "tier": "闲时" if tier is PRICE["off"] else "忙时"}


# ---------------------------------------------------------------- CLI
def _read_prompt(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if args.prompt:
        return " ".join(args.prompt)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def main():
    ap = argparse.ArgumentParser(description="百度千帆 ERNIE 客户端")
    ap.add_argument("prompt", nargs="*", help="提问内容")
    ap.add_argument("--file", help="从文件读取 prompt")
    ap.add_argument("--system", help="system 提示词")
    ap.add_argument("--model", help=f"模型 ID，默认 {DEFAULT_MODEL}")
    ap.add_argument("--stream", action="store_true", help="流式输出")
    ap.add_argument("--think", action="store_true", help="开启深度思考（默认关闭，思考 token 按输出计费）")
    ap.add_argument("--json", action="store_true", help="要求输出 JSON（response_format）")
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--max-tokens", type=int)
    ap.add_argument("--usage", action="store_true", help="打印 token 用量与费用估算")
    ap.add_argument("--check", action="store_true", help="连通性自检")
    ap.add_argument("--set-key", help="写入 API Key 到配置文件并退出")
    args = ap.parse_args()

    if args.set_key:
        p = save_api_key(args.set_key)
        print(f"✅ API Key 已写入 {p}（权限 600）")
        return 0

    cfg = load_config()

    if args.check:
        print(f"配置文件：{CONFIG_PATH}")
        print(f"端点：{cfg.get('endpoint')}")
        print(f"模型：{cfg.get('model')}")
        print(f"API Key：{'已配置 (' + cfg['api_key'][:12] + '…)' if cfg.get('api_key') else '❌ 未配置'}")
        if not cfg.get("api_key"):
            print("\n请先设置密钥：python3 scripts/ernie.py --set-key 'bce-v3/ALTAK-...'")
            return 2
        # 关闭思考 + 给足预算，避免推理占满导致 content 为空的“假失败”；偶发空正文再重试一次
        result = ""
        r = {}
        for attempt in range(2):
            r = chat([{"role": "user", "content": "只回复两个字：连通"}], cfg=cfg,
                     max_tokens=64, thinking={"type": "disabled"})
            result = (r["content"] or "").strip()
            if result:
                break
        print(f"\n返回：{result!r}")
        if not result:
            print("⚠️ 两次请求都返回空正文：可能是模型侧的思考型输出波动，稍后重试或换 --max-tokens。",
                  file=sys.stderr)
            return 3
        print(f"用量：{r['usage']}")
        print(f"费用估算：{cost_estimate(r['usage'])}")
        return 0

    prompt = _read_prompt(args)
    if not prompt:
        ap.print_help()
        return 2

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": prompt})

    kw = {}
    if args.temperature is not None:
        kw["temperature"] = args.temperature
    if args.max_tokens is not None:
        kw["max_tokens"] = args.max_tokens
    if args.json:
        kw["response_format"] = {"type": "json_object"}
    if args.think:
        kw["thinking"] = {"type": "enabled"}

    try:
        if args.stream:
            for piece in stream_chat(messages, model=args.model, cfg=cfg, **kw):
                sys.stdout.write(piece)
                sys.stdout.flush()
            print()
            return 0
        r = chat(messages, model=args.model, cfg=cfg, **kw)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    print(r["content"])
    if r.get("warning"):
        print(f"⚠️ {r['warning']}", file=sys.stderr)
    if args.usage:
        print(f"\n--- model: {r['model']} | usage: {r['usage']} | 费用: {cost_estimate(r['usage'])}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
