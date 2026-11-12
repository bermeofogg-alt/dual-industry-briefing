#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wizshot-ME 任务生成器：本地人像 + 人声样音 + 一句台词 → 可直接提交的 job.json
===========================================================================
解决三个最容易白花钱的坑：
  1. 素材必须是【公网 URL】，本地路径一律不收；
  2. 人声 wav 必须 10–60s，台词总时长 4–16s（单段 ≤450 字节）；
  3. 提交一次约 ¥7，先离线预检再花钱。

两种模式：
  A. 从本地素材生成任务（推荐）
     python3 scripts/wizshot_job.py \
       --portrait ~/Desktop/主播.png \
       --voice   ~/Desktop/样音.wav \
       --text    "这套被子一摸就不想撒手，软得像陷进云里。" \
       --out     .state/wizshot-job.json

  B. 校验已有 job.json（不联网、不计费）
     python3 scripts/wizshot_job.py --validate .state/wizshot-job.json

素材会被复制到项目根的 wizshot-assets/（不在 git 提交范围内），URL 用已发布站点的
sharecode 直出链接。复制后需【重新发布一次站点】，千帆服务器才抓得到；见 README。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
PUB_DIR = PROJ / "wizshot-assets"
DEFAULT_BASE_URL = "https://dual-industry-briefing-19330.app.workbuddy.host/wizshot-assets"
DEFAULT_SHARECODE = "TUWUFE6BRX"
MODEL = "ernie-wizshot-me"
PRICE_PER_SEC = 0.7

DEFAULTS = {
    "name": "主播",
    "identity": "家纺品牌带货主播",
    "temperament": "亲切松弛、真诚自然",
    "camera": "正面机位，平视中近景",
    "emotion": "开场惊喜亲近，讲到卖点时放松笃定，收尾轻快带笑意",
    "performance": "开场眼睛微微睁大、身体前倾；讲到卖点时手掌轻拍产品；收尾点头看向镜头",
    "voice_settings": "带货快语速，开头稍提亮，关键词放慢半拍，尾音轻快上扬",
}


# ---------------------------------------------------------------- 素材检查
def _image_size(path):
    """用 macOS 自带 sips 读图片尺寸，失败返回 None。"""
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            stderr=subprocess.DEVNULL, timeout=10, text=True,
        )
        w = re.search(r"pixelWidth:\s*(\d+)", out)
        h = re.search(r"pixelHeight:\s*(\d+)", out)
        if w and h:
            return int(w.group(1)), int(h.group(1))
    except Exception:
        pass
    return None


def _wav_info(path):
    """返回 (时长秒, 采样率, 声道数, 位深)；非 PCM wav 返回 None。"""
    try:
        with wave.open(str(path), "rb") as w:
            sec = w.getnframes() / float(w.getframerate())
            return sec, w.getframerate(), w.getnchannels(), w.getsampwidth() * 8
    except Exception:
        return None


def check_local(portrait, voice):
    errors, warns, info = [], [], []
    if portrait:
        if not Path(portrait).is_file():
            errors.append(f"人像不存在：{portrait}")
        elif Path(portrait).suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            errors.append("人像只支持 JPEG / PNG / WEBP")
        else:
            size = _image_size(portrait)
            if size:
                w, h = size
                info.append(f"人像 {w}×{h}，短边 {min(w, h)}px，宽高比 {w / h:.2f}")
                if min(w, h) < 720:
                    errors.append(f"人像短边 {min(w, h)}px < 720px，会被服务端拒绝")
                ratio = w / h
                if ratio < 9 / 16 or ratio > 16 / 9:
                    warns.append("图片宽高比超出 9:16～16:9，建议裁成竖版 9:16")
            else:
                warns.append("无法读取图片尺寸（sips 不可用），请自行确认短边 ≥720px")
    if voice:
        if not Path(voice).is_file():
            errors.append(f"人声样音不存在：{voice}")
        elif Path(voice).suffix.lower() != ".wav":
            errors.append("人声样音必须是 .wav（不是 mp3/m4a）")
        else:
            w = _wav_info(voice)
            if not w:
                errors.append("无法解析 wav，请转成 PCM 编码的 wav：afconvert -f WAVE -d LEI16 input.m4a output.wav")
            else:
                sec, rate, ch, bits = w
                info.append(f"人声样音 {sec:.1f}s / {rate}Hz / {ch}声道 / {bits}bit")
                if not (10 <= sec <= 60):
                    errors.append(f"人声样音 {sec:.1f}s，必须 10–60s（这是音色克隆样本，不是最终台词音频）")
    return errors, warns, info


# ---------------------------------------------------------------- payload 检查
def check_payload(payload):
    errors, warns, info = [], [], []
    if payload.get("model") != MODEL:
        warns.append(f"model={payload.get('model')!r}，建议固定为 {MODEL}")
    personas = payload.get("personas") or {}
    if not personas:
        errors.append("缺 personas（至少一个出镜人物）")
        return errors, warns, info

    urls = []
    for name, p in personas.items():
        for key in ("mid", "avatar_url"):
            u = str(p.get(key, ""))
            if not u.startswith("http"):
                errors.append(f"personas[{name}].{key} 不是公网 URL：{u!r}（本地路径和 base64 都不接受）")
            elif "<" in u or "example" in u.lower():
                errors.append(f"personas[{name}].{key} 还是模板占位符：{u}")
            else:
                urls.append((f"personas[{name}].{key}", u))

    dialogs, total_bytes = [], 0
    shots_n = 0
    for fr in payload.get("fragments") or []:
        for sh in fr.get("shots") or []:
            shots_n += 1
            img = str((sh.get("camera_settings") or {}).get("shot_image", ""))
            if not img.startswith("http"):
                errors.append(f"shot_image 不是公网 URL：{img!r}")
            elif "<" in img:
                errors.append(f"shot_image 还是模板占位符：{img}")
            else:
                urls.append(("shot_image", img))
            for ch in sh.get("characters") or []:
                if ch not in personas:
                    errors.append(f"characters 里的 {ch!r} 不在 personas 中（画外音不算出镜人物）")
            for seg in sh.get("segments") or []:
                if seg.get("character_speaker") not in personas:
                    errors.append(f"character_speaker={seg.get('character_speaker')!r} 不在 personas 中")
                d = (seg.get("production_elements") or {}).get("dialog", "")
                dialogs.append(d)
                b = len(d.encode("utf-8"))
                total_bytes += b
                if b > 450:
                    errors.append(f"单段 dialog {b} 字节 > 450，请拆成两段或精简")
    if not dialogs:
        errors.append("没有任何台词（segments 为空）")
    if not shots_n:
        errors.append("没有任何分镜（shots 为空）")

    chars = sum(len(d) for d in dialogs)
    est = max(4, min(16, round(chars / 4.5))) if chars else 0
    if chars:
        info.append(f"台词 {chars} 字 / {total_bytes} 字节，估算 {est}s，费用约 ¥{est * PRICE_PER_SEC:.1f}")
        if chars < 20:
            warns.append("台词偏短（<20 字），可能凑不满 4s 下限")
        if chars > 70:
            warns.append("台词偏长（>70 字），可能超过 16s 上限，建议 25–55 字")
    return errors, warns, info


def _report(errors, warns, info):
    for s in info:
        print(f"  · {s}")
    for s in warns:
        print(f"  ⚠️ {s}")
    for s in errors:
        print(f"  ❌ {s}")
    return not errors


# ---------------------------------------------------------------- 生成
def build(args):
    ts = time.strftime("%Y%m%d-%H%M%S")
    PUB_DIR.mkdir(parents=True, exist_ok=True)

    def publish(src, tag):
        p = Path(os.path.expanduser(src))
        dst = PUB_DIR / f"{tag}-{ts}{p.suffix.lower()}"
        shutil.copy2(p, dst)
        return dst

    portrait_file = publish(args.portrait, "portrait") if not args.portrait_url else None
    voice_file = publish(args.voice, "voice") if not args.voice_url else None

    def url(local_url, f):
        if local_url:
            return local_url
        tail = f"?sharecode={args.sharecode}" if args.sharecode else ""
        return f"{args.base_url.rstrip('/')}/{f.name}{tail}"

    portrait_url = url(args.portrait_url, portrait_file)
    voice_url = url(args.voice_url, voice_file)
    name = args.name

    payload = {
        "model": MODEL,
        "personas": {
            name: {
                "mid": voice_url,
                "avatar_url": portrait_url,
                "name": name,
                "identity": args.identity,
                "temperament": args.temperament,
            }
        },
        "fragments": [{
            "shots": [{
                "camera_settings": {"camera_movement": args.camera, "shot_image": portrait_url},
                "characters": [name],
                "segments": [{
                    "character_speaker": name,
                    "production_elements": {
                        "dialog": args.text,
                        "emotion": args.emotion,
                        "performance": args.performance,
                        "voice_settings": args.voice_settings,
                    },
                }],
            }]
        }],
    }

    print("【本地素材预检】")
    e1, w1, i1 = check_local(
        args.portrait if not args.portrait_url else None,
        args.voice if not args.voice_url else None,
    )
    print("【任务参数预检】")
    e2, w2, i2 = check_payload(payload)
    ok = _report(e1 + e2, w1 + w2, i1 + i2)
    if not ok:
        print("\n预检未通过，未写出 job.json（避免白花 ¥7）。修好后重跑。")
        return 1

    out = Path(os.path.expanduser(args.out))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 任务文件：{out}")
    if portrait_file or voice_file:
        print(f"   素材已复制：{PUB_DIR}/")
        print("   ⚠️ 下一步必须先【重新发布站点】，否则千帆抓不到这两个 URL。")
    print("\n【提交命令】")
    print(f"  python3 scripts/wizshot.py --payload {out} --output ~/Desktop/wizshot-{ts}.mp4 --yes")
    return 0


def validate(path):
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        print(f"❌ 找不到 {p}")
        return 1
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ JSON 解析失败：{e}")
        return 1
    print(f"【离线预检】{p}")
    e, w, i = check_payload(payload)
    ok = _report(e, w, i)
    print("\n" + ("✅ 可以提交（鉴权请另跑 python3 scripts/wizshot.py --check）" if ok else "❌ 请修好上面的错误再提交"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Wizshot-ME 任务生成 / 离线预检")
    ap.add_argument("--validate", help="只校验已有 job.json，不联网、不计费")
    ap.add_argument("--portrait", help="本地人像图片（正面清晰半身照，短边 ≥720px）")
    ap.add_argument("--voice", help="本地人声样音 wav（10–60s，含人声）")
    ap.add_argument("--text", help="台词，建议 25–55 字")
    ap.add_argument("--out", default=".state/wizshot-job.json", help="job.json 输出路径")
    ap.add_argument("--portrait-url", help="已有公网人像 URL（给了就不复制本地文件）")
    ap.add_argument("--voice-url", help="已有公网 wav URL")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL, help="素材公网目录")
    ap.add_argument("--sharecode", default=DEFAULT_SHARECODE, help="站点分享码，空字符串表示不需要")
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), default=v)
    args = ap.parse_args()

    if args.validate:
        return validate(args.validate)
    if not args.text or not (args.portrait or args.portrait_url) or not (args.voice or args.voice_url):
        ap.print_help()
        print("\n❌ 至少需要 --portrait(或 --portrait-url)、--voice(或 --voice-url)、--text")
        return 2
    return 0 if build(args) == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        sys.exit(130)
    except (OSError, RuntimeError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
