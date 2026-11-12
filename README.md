# 家纺&零售每日晨报（dual-industry-briefing）

宜爱家出品的每日行业晨报站点。**数据与版式分离**：每天只改 `data/<日期>.json`，页面由 `build.py` 渲染。

## 目录结构

```
dual-industry-briefing/
├── build.py                # 渲染脚本：data/<date>.json → index.html
├── index.html              # 生成产物（不要手改，会被覆盖）
├── assets/
│   ├── style.css           # 宜爱家绿色设计系统（版式唯一定义处）
│   ├── logo.txt            # 品牌 logo（data URI）
│   └── favicon.txt         # favicon（data URI）
└── data/
    └── 2026-11-12.json     # 每日内容数据
```

## 每日流程

```bash
cd /Users/jiangjuji/WorkBuddy/dual-industry-briefing
python3 build.py 2026-11-13          # 不传日期则取 data/ 下最新
```

然后发布（sites）：`directory=本目录`、`domainPrefix=dual-industry-briefing`、`language=static`、`entryHtml=index.html`。

## 数据 schema

```jsonc
{
  "date": "2026-11-12",
  "weekday": "周四",
  "modules": {
    "home": {                        // 家纺行业
      "name": "家纺行业",
      "coverage": "覆盖无印良品 / 全棉时代 …",
      "notice": "口径说明正文",
      "sections": [
        { "key": "brand-action", "name": "品牌动作", "items": [ /* item */ ] },
        { "key": "industry", "name": "行业研究", "role": "research", "items": [] }
      ]
    },
    "retail": { /* 商业零售洞察，结构同 home */ }
  },
  "quotes": [ { "text": "金句正文（不含引号）", "source": "来源媒体" } ]
}
```

item 字段：`brand`、`color`、`tag`、`title`、`summary`、`time`、`source`、`url`、`new`。

约定：
- `role: "research"` 的段落计入「行业研究」统计，其余计入「品牌动作」。
- 卡片编号、品牌筛选按钮、顶部统计、页脚统计全部由脚本按数据自动生成，无需手填。
- 品牌筛选条在品牌数 > 2 时自动出现。

## 内容红线

1. 每条必须有可点开的真实 URL 与明确来源媒体，**查不到就跳过**，并在 `notice` 注明「本期 XX 无新增公开信源」。
2. 金句是基于真实报道的**洞察提炼**，不是原文摘录，页面已有免责说明。
3. 版式与配色改动只动 `assets/style.css`。

## 迁移提示

定时任务保存在**创建它的那台机器本地**，换电脑不会自动跟着走。迁移到新机器时：

1. 拷贝整个项目目录；
2. 重建定时任务（每天 06:30），prompt 里写明：检索品牌清单 → 写 `data/<日期>.json` → `python3 build.py` → 发布 → 输出链接 + 文字摘要。

## GitHub 同步与飞书推送（2026-11-12 于 Mac 重建）

原 Windows 端的凭证与配置未随迁移带来，已在 Mac 端重建流程骨架：

```bash
# 1) 推送 GitHub（首次需先在 github.com/jiangjuji 下创建空仓库 dual-industry-briefing）
./scripts/push_github.sh

# 2) 推送飞书群
./scripts/notify_feishu.sh "家纺&零售每日晨报 11-12" "家纺精选：… 零售精选：…" "https://…app.workbuddy.host/…"
```

凭证约定（放用户目录，不进仓库、不会被提交）：

| 项目 | 配置 | 用途 |
| --- | --- | --- |
| GitHub 仓库 | `github.com/bermeofogg-alt/dual-industry-briefing`（main 分支） | 每日数据与产物备份 |
| GitHub 认证 | GitHub CLI 设备授权（`gh auth login`），git credential helper 已配置 | push 认证，无需手工管理 PAT |
| `~/.config/dual-industry-briefing/feishu.webhook` | 飞书群机器人 webhook 地址 | 群消息推送 |

网络：git 已配置走本机 Clash 代理 `http://127.0.0.1:7890`（GitHub 直连不稳定）。

每日自动化的流程已从「检索→写数据→渲染→发布」扩展为「检索→写数据→渲染→发布→push GitHub→飞书推送」，飞书 webhook 到位后生效。

## 百度千帆 ERNIE 模型接入（2026-11-12）

用于给晨报做辅助生成：金句提炼、摘要压缩、飞书文案改写、JSON 结构化等。

| 项目 | 值 |
| --- | --- |
| 端点 | `POST https://qianfan.baidubce.com/v2/chat/completions` |
| 模型 ID | `ernie-5.5-flash-preview`（1M 上下文，RPM 300 / TPM 3,000,000） |
| 鉴权 | `Authorization: Bearer <API Key>`，Key 形如 `bce-v3/ALTAK-xxxx/yyyy` |
| 价格 | 输入 忙时 ¥2 / 闲时 ¥1 每百万 token；输出 忙时 ¥8 / 闲时 ¥4。**闲时 22:00–次日 08:00** |
| 客户端 | `scripts/ernie.py`（纯标准库，无第三方依赖） |
| 配置 | `~/.config/dual-industry-briefing/ernie.json`（权限 600，不在仓库内） |

### 配置密钥（二选一）

```bash
# 方式 A：写入配置文件（推荐，长期有效）
python3 scripts/ernie.py --set-key 'bce-v3/ALTAK-xxxx/yyyy'

# 方式 B：临时环境变量
export QIANFAN_API_KEY='bce-v3/ALTAK-xxxx/yyyy'
```

密钥在 [千帆控制台 → 快速接入](https://console.bce.baidu.com/qianfan/overview) 页创建「通用 API Key」，并确认该 Key 已开通 `ernie-5.5-flash-preview`。

### 用法

```bash
python3 scripts/ernie.py --check                                  # 连通性自检（推荐先跑这个）
python3 scripts/ernie.py "用一句话总结今天的家纺动态"
python3 scripts/ernie.py --system "你是家纺行业分析师" --usage "…"
python3 scripts/ernie.py --stream "写一段晨报导语"                 # 流式输出
python3 scripts/ernie.py --json "输出 {\"brand\":\"\",\"action\":\"\"}"  # 强制 JSON
python3 scripts/ernie.py --file prompt.txt --temperature 0.3
python3 scripts/ernie.py --think "分析这段财报" --max-tokens 2048    # 开启深度思考
```

### 思考型模型的坑（实测）

`ernie-5.5-flash-preview` 是思考型模型，**思考 token 计入输出计费**，且会挤占 `max_tokens` 预算：

- `max_tokens=16` 时经常出现 HTTP 200 但 `content` 为空（预算全被推理吃掉），看起来像"调用失败"。
- `thinking: {"type": "disabled"}` 能大幅降低推理量，但**不是硬保证**，实测仍偶发 200+ 推理 token；`enable_thinking: false` 完全无效。
- 客户端已内置两层兜底：默认带 `thinking:disabled`；一旦返回空正文就自动放大预算重试一次（最多一次）。自检 `--check` 另有一次重试。

因此配置文件里有 `"thinking": "disabled"`，需要深度推理时用 CLI 加 `--think` 并给足 `--max-tokens`（建议 ≥ 2048）。日常摘要/改写保持默认即可，成本和空输出风险都最低。

作为模块调用：

```python
from ernie import chat, cost_estimate
r = chat([{"role": "user", "content": "你好"}])
print(r["content"], r["usage"], cost_estimate(r["usage"]))
```

### 兼容 OpenAI SDK

千帆 v2 协议兼容 OpenAI，可直接用官方 SDK：

```python
from openai import OpenAI
client = OpenAI(
    api_key="bce-v3/ALTAK-xxxx/yyyy",
    base_url="https://qianfan.baidubce.com/v2",
)
client.chat.completions.create(
    model="ernie-5.5-flash-preview",
    messages=[{"role": "user", "content": "你好"}],
)
```

第三方工具（Cherry Studio / Cursor / Chatbox 等）填：Base URL `https://qianfan.baidubce.com/v2`、API Key 同上、Model `ernie-5.5-flash-preview`。

### 排错对照

| 返回 | 含义 | 处理 |
| --- | --- | --- |
| 401 `invalid_iam_token` | Key 本身无效（拼错/已删/带空格） | 重新复制或新建 Key |
| 403 权限类 | Key 未绑定该模型 | 控制台给 Key 绑定模型 |
| 429 | 限流或额度用尽 | 退避重试 / 续费 |
| 连接超时 | 走了代理 | 配置里 `proxy` 留空即强制直连 |

> 千帆是国内域名，`notify_feishu.sh`、git 用的 Clash 代理**不要**套到 ERNIE 调用上；`scripts/ernie.py` 在 `proxy` 为空时会显式绕过系统代理直连（实测 0.15s 返回）。

## ERNIE-Wizshot-ME 视频生成模型（2026-11-12）

文心一镜微表情大模型：让静态人像开口说话，生成 4–15 秒 1080p 真人口播视频。**异步接口，返回 `task_id` 后轮询取结果**。

| 项目 | 值 |
| --- | --- |
| 创建任务 | `POST https://qianfan.baidubce.com/v2/mm/ernie/ernie-wizshot-me` |
| 查询任务 | `GET https://qianfan.baidubce.com/v2/mm/ernie/tasks?task_id=xxx` |
| model | `ernie-wizshot-me` |
| 状态 | `pending` → `processing` → `succeeded` / `failed` |
| 计费 | **¥0.7/秒**，10 秒约 ¥7；并发 1、队列 1 |
| 客户端 | `scripts/wizshot.py` |

⚠️ **这不是对话模型**，协议不是 `chat/completions`，**不要写进 WorkBuddy 的自定义模型列表 `models.json`**，否则会被当聊天模型调用而必然失败。它是项目级脚本能力。

```bash
python3 scripts/wizshot.py --check                       # 零成本自检（不生成、不计费）
python3 scripts/wizshot.py --example > job.json         # 导出 payload 模板
python3 scripts/wizshot.py --payload job.json --output ~/Desktop/ad.mp4 --yes
python3 scripts/wizshot.py --task-id <id> --status      # 只查状态
python3 scripts/wizshot.py --task-id <id> --output ~/Desktop/ad.mp4  # 补下载
```

### 三个硬约束

1. **素材必须是公网可访问的 URL**，不接受本地路径，也不接受 base64。`avatar_url` / `shot_image` 为 JPEG/PNG/WEBP（短边 ≥720px，宽高比 9:16～16:9）；`mid` 为含人声的 wav、时长 10–60s。千帆 AppBuilder 的「文件上传」接口返回的是 `file_id`，**不能**当 URL 用。
2. **台词总时长 4–16s**（服务端实测），中文按 4 字/秒估算，带货快语速 5 字/秒 → 建议 25–55 字；单段 `dialog` ≤ 450 字节。
3. **分镜图人物与 avatar 穿着一致、需含清晰头像**，且 `characters` 必须是出镜人物（画外音不算）。

`--check` 的原理是提交一个缺 `personas`/`fragments` 的请求，服务端返回 400 `invalid_video_generation_argument` 即证明鉴权、路径、模型权限全部就绪，全程不产生视频费用。

### 典型错误码

| 错误 | 处理 |
| --- | --- |
| `video_generation_concurrency_exceeded` (429) | 并发 1、队列 1，等上个任务跑完 |
| `video_generation_prompt_unsafe` (403) | 输入图或文案被安全策略拦截，换素材 |
| `invalid_video_generation_argument` (400) | 参数不合法，重点查时长与图片 URL 可达性 |

### 下次怎么调用（2026-11-13 补）

**先分清两条链路**，别再找错入口：

| 你要的效果 | 用哪个 | 在哪调用 |
| --- | --- | --- |
| 一张商品图 → 10 秒氛围带货片 | 图生视频（VideoGen） | 对话里直接说「用这张图生成 N 秒竖屏视频」 |
| 一张真人半身照 → 开口念台词的口播 | **Wizshot-ME** | `scripts/wizshot_job.py` + `scripts/wizshot.py` |
| 写文案、问答、总结 | ERNIE-5.5-Flash | WorkBuddy 模型下拉 或 `scripts/ernie.py` |

⚠️ Wizshot-ME **不会出现在模型下拉列表里，也不要加进 `models.json`**——它是异步任务协议，不是 `chat/completions`。上次那支 10 秒家纺带货片是 VideoGen 做的，Wizshot-ME 一次都还没真正出过片。

**入口 1｜对话一句话（最省事）**：直接说

> 用 Wizshot-ME 做口播视频：人像 `~/Desktop/主播.png`，样音 `~/Desktop/样音.wav`，台词「……」，输出到桌面

我会自动完成：复制素材 → 重新发布站点 → 离线预检 → 鉴权自检 → 提交 → 轮询 → 下载到桌面。

**入口 2｜命令行三步**

```bash
# 1) 本地素材 + 台词 → job.json（自动校验图片尺寸、wav 时长、台词字节数）
python3 scripts/wizshot_job.py \
  --portrait ~/Desktop/主播.png \
  --voice   ~/Desktop/样音.wav \
  --text    "这套被子一摸就不想撒手，软得像陷进云里，今天下单还送同款收纳袋。" \
  --out     .state/job.json

# 2) 素材公网化：在对话里说「发布站点」，或自行执行一次 sites 发布；然后确认 URL 是 200
curl -o /dev/null -w "%{http_code}\n" "https://dual-industry-briefing-19330.app.workbuddy.host/wizshot-assets/portrait-<时间戳>.png?sharecode=TUWUFE6BRX"

python3 scripts/wizshot_job.py --validate .state/job.json   # 任何时候可复查任务文件

# 3) 自检 + 提交（--yes 表示确认 ¥0.7/秒的费用）
python3 scripts/wizshot.py --check
python3 scripts/wizshot.py --payload .state/job.json --output ~/Desktop/ad.mp4 --yes
```

**入口 3｜Python 代码里调用**

```python
import sys; sys.path.insert(0, "scripts")
import wizshot
tid, raw = wizshot.create(payload)          # POST 建任务
r = wizshot.wait(tid)                       # 轮询到 succeeded/failed
url = wizshot.find_video_urls(r.get("content") or r)[0][1]
wizshot.download(url, "~/Desktop/ad.mp4")
```

**素材公网 URL（2026-11-13 实测）**：站点不带 `sharecode` 返回 403，**带 `?sharecode=TUWUFE6BRX` 返回 200** → 默认方案是把素材放进 `wizshot-assets/` 后重新发布站点；`raw.githubusercontent.com` 从国内直连不通（HTTP 000），**不要**拿 GitHub raw 当素材 URL。若有自己的 COS/OSS/七牛，用 `--portrait-url` / `--voice-url` 直接传公网链接即可，跳过复制与发布。若重新发布后分享码变了，用 `--sharecode 新码` 重新生成 job.json。

⚠️ 首次使用务必先跑第 2 步的 `curl` 验证：素材目录是新增的，**只有重新发布过站点才会存在**。若返回 404，说明这次发布没带上该目录，先解决发布再提交，否则参数错误也可能计费。`wizshot-assets/` 故意不写进 `.gitignore`（否则站点发布会把素材一起跳过），改由 `push_github.sh` 的 `git reset -- wizshot-assets` 兜底，人像与人声不会被推到公开仓库；**不要**手动执行 `git add -A`。

**提交前四项自检**（一次约 ¥7，参数错了也可能计费）：
1. `python3 scripts/wizshot_job.py --validate .state/job.json` 全绿；
2. `python3 scripts/wizshot.py --check` 显示鉴权有效；
3. 两个素材 URL 用 `curl` 裸请求（不带 cookie）都返回 200；
4. 人像正面清晰半身、样音 10–60s 含人声、台词 25–55 字。

补充：手上的样音若是 m4a/mp3，先转成 PCM wav 再传：`afconvert -f WAVE -d LEI16 input.m4a output.wav`；样音是**音色克隆样本**、10–60s，不是最终台词音频。

