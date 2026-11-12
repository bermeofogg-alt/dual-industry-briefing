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

