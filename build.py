#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 data/<date>.json 渲染成 index.html。

用法:
    python3 build.py                # 用 data/ 下日期最新的 json
    python3 build.py 2026-11-12     # 指定日期

设计原则：内容（JSON）与版式（本脚本 + assets/style.css）分离，
每天只需更新 JSON，页面结构与视觉保持不变。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

ICONS = {
    "brand-action": '<svg viewBox="0 0 24 24"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>',
    "industry": '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><path d="M14 2v6h6M9 13h6M9 17h6" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>',
    "quote": '<svg viewBox="0 0 24 24"><path d="M7 7h4v6H8v-2h2c0 2-1 3-3 3v-2h1V7zm8 0h4v6h-3v-2h2c0 2-1 3-3 3v-2h1V7z" fill="#fff"/></svg>',
}
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M9 7h8v8"/></svg>'
MODULE_ORDER = ["home", "retail"]
MODULE_LABEL = {"home": "家纺行业", "retail": "商业零售洞察"}


def esc(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def load(date: str | None) -> tuple[dict, str]:
    files = sorted(DATA.glob("*.json"))
    if not files:
        sys.exit("data/ 下没有 json")
    if date:
        p = DATA / f"{date}.json"
        if not p.exists():
            sys.exit(f"找不到 {p}")
    else:
        p = files[-1]
    return json.loads(p.read_text(encoding="utf-8")), p.stem


def render_card(item: dict, num: int, module: str) -> str:
    new_cls = " new-card" if item.get("new") else ""
    badge = '<span class="new-badge">新动态</span>' if item.get("new") else ""
    url = item.get("url", "#")
    return f'''      <article class="card{new_cls}" data-brand="{esc(item['brand'])}" data-module="{module}">
        <span class="card-num">{num:02d}</span>
        <div class="chip-row"><span class="brand-chip" style="background:{item.get('color','#3CB444')}">{esc(item['brand'])}</span><span class="sec-tag">{esc(item.get('tag',''))}</span>{badge}</div>
        <h3 class="card-title">{esc(item['title'])}</h3>
        <p class="card-summary">{esc(item['summary'])}</p>
        <div class="card-meta"><span class="card-time">📅 {esc(item.get('time',''))}</span><span class="card-source">{esc(item.get('source',''))}</span></div>
        <div class="card-actions">
          <a class="card-link" href="{esc(url)}" data-copy="{esc(url)}" target="_blank" rel="noopener noreferrer" aria-label="阅读原文：{esc(item['title'])}">阅读原文 {ARROW}</a>
          <button type="button" class="copy-btn" data-copy="{esc(url)}">🔗 复制链接</button>
        </div>
      </article>'''


def build(doc: dict) -> str:
    date = doc["date"]
    weekday = doc.get("weekday", "")
    mods = doc["modules"]

    # ---- 计数 ----
    per_mod = {}
    research_total = 0
    for key in MODULE_ORDER:
        items = [it for sec in mods[key]["sections"] for it in sec["items"]]
        per_mod[key] = len(items)
        research_total += sum(len(s["items"]) for s in mods[key]["sections"]
                              if s.get("role") == "research")
    total = sum(per_mod.values())
    quotes = doc.get("quotes", [])
    new_count = sum(1 for key in MODULE_ORDER for sec in mods[key]["sections"]
                    for it in sec["items"] if it.get("new"))

    # ---- 顶部导航 ----
    nav = [f'      <span class="nav-group-label" style="color:#3CB444">{MODULE_LABEL["home"]}</span>']
    nav.append('      <button type="button" data-target="home-brand-action">品牌动作</button>')
    nav.append('      <button type="button" data-target="home-industry">行业研究</button>')
    nav.append(f'      <span class="nav-group-label" style="color:#1E7E32">{MODULE_LABEL["retail"]}</span>')
    nav.append('      <button type="button" data-target="retail-brand-action">品牌动作</button>')
    nav.append('      <button type="button" data-target="retail-industry">行业研究</button>')
    nav.append('      <span class="nav-group-label" style="color:#3CB444">提炼</span>')
    nav.append('      <button type="button" data-target="quotes">今日金句</button>')
    nav_html = "\n".join(nav)

    # ---- 主体 ----
    bodies = []
    counter = 1
    for key in MODULE_ORDER:
        m = mods[key]
        sections = m["sections"]
        brand_sec = sum(len(s["items"]) for s in sections if s.get("role") != "research")
        res_sec = sum(len(s["items"]) for s in sections if s.get("role") == "research")

        # 品牌筛选条
        seen, btns = set(), []
        for sec in sections:
            for it in sec["items"]:
                if it["brand"] in seen:
                    continue
                seen.add(it["brand"])
                btns.append(f'  <button type="button" class="bf" data-module="{key}" data-brand="{esc(it["brand"])}" style="--bc:{it.get("color","#3CB444")}">{esc(it["brand"])}</button>')
        brandbar = "\n".join(btns) if len(seen) > 2 else ""

        sec_html = []
        for sec in sections:
            sid = f"{key}-{sec['key']}"
            cards = "\n".join(render_card(it, counter + i, key) for i, it in enumerate(sec["items"]))
            counter += len(sec["items"])
            icon = ICONS["industry"] if sec.get("role") == "research" else ICONS["brand-action"]
            sec_html.append(f'''    <section class="section" id="{sid}">
    <div class="section-inner">
      <div class="section-head">
        <span class="icon">{icon}</span>
        <h2>{esc(sec['name'])}</h2>
        <span class="count">{len(sec['items'])} 条</span>
      </div>
      <div class="cards">
{cards}
      </div>
    </div>
    </section>''')

        notice_cls = "notice notice-retail" if key == "retail" else "notice"
        notice = ""
        if m.get("notice"):
            notice = f'<div class="{notice_cls}"><strong>口径说明：</strong>{m["notice"]}</div>'

        bodies.append(f'''<div class="module" data-module="{key}">
<div class="module-banner {key}">
  <div class="module-banner-inner">
    <h2>{esc(m['name'])} <span class="m-total">· {per_mod[key]} 条</span></h2>
    <p class="mtag">{esc(m.get('coverage',''))}</p>
    <div class="mchips">
      <span class="mchip">品牌动作 {brand_sec}</span>
      <span class="mchip">行业研究 {res_sec}</span>
    </div>
  </div>
</div>
{brandbar and f'<div class="brandbar">' + chr(10) + '  <span class="lbl">按品牌筛选：</span>' + chr(10) + brandbar + chr(10) + '</div>'}
{notice}
{chr(10).join(sec_html)}
</div>''')

    # ---- 金句 ----
    q_cards = "\n".join(
        f'''      <article class="quote-card">
        <span class="quote-num">金句 {i:02d}</span>
        <p class="quote-text">“{esc(q['text'])}”</p>
        <span class="quote-source">据 {esc(q.get('source',''))} 报道提炼</span>
      </article>''' for i, q in enumerate(quotes, 1))

    quotes_html = ""
    if quotes:
        quotes_html = f'''<section class="section quotes-section" id="quotes">
  <div class="section-inner">
    <div class="section-head">
      <span class="icon quote-icon">{ICONS['quote']}</span>
      <h2>今日金句提炼</h2>
      <span class="count">{len(quotes)} 句</span>
    </div>
    <div class="quotes-grid">
{q_cards}
    </div>
    <p class="quotes-note">＊ 以上为基于本期真实报道的<strong>洞察提炼</strong>，非逐字引用；每条标注原始信源，便于溯源核对。</p>
  </div>
</section>'''

    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    favicon = (ASSETS / "favicon.txt").read_text(encoding="utf-8").strip()
    logo = (ASSETS / "logo.txt").read_text(encoding="utf-8").strip()

    legend = ""
    if new_count:
        legend = f'''<div class="legend-bar">
  <span class="legend-dot"></span>
  <span>带 <b>「新动态」</b> 标记为今日新增内容；<b>无标记</b>即此前已报道，可跳过不重复阅读。</span>
  <span class="legend-count">本期新动态 {new_count} 条</span>
</div>'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>家纺&零售每日晨报 · {date}</title>
<meta name="description" content="宜爱家出品 · 家纺与商业零售每日晨报：真实信源聚合品牌动态、行业研究与今日金句。">
<meta property="og:site_name" content="宜爱家">
<meta property="og:title" content="家纺&零售每日晨报">
<meta property="og:description" content="宜爱家出品 · 家纺 + 商业零售 · 真实垂直信源每日聚合 · {date}">
<meta property="og:type" content="website">
<link rel="icon" type="image/png" href="{favicon}">
<script>document.documentElement.classList.add('js-ready');</script>
<style>{css}</style>
</head>
<body>
<nav class="topnav" aria-label="版块导航">
  <div class="topnav-inner">
    <div class="topnav-brand"><img class="nav-logo" src="{logo}" alt="宜爱家 Famhom"><span>宜爱家 · 每日晨报</span></div>
    <div class="topnav-links">
{nav_html}
    </div>
  </div>
</nav>

<header class="hero">
  <div class="hero-inner">
    <div class="date-badge"><span class="live"></span>{date.replace('-', '年', 1).replace('-', '月')}日 · {weekday} · 北京时间</div>
    <h1>家纺&零售 <span class="accent">每日晨报</span></h1>
    <p class="hero-tagline">宜爱家出品 · 家纺行业 + 商业零售洞察 · 真实垂直信源聚合（WebSearch）</p>
    <div class="hero-stats">
      <div class="stat-card"><div class="stat-num" data-target="{total}">0</div><div class="stat-label">资讯条数</div></div>
      <div class="stat-card"><div class="stat-num" data-target="{per_mod['home']}">0</div><div class="stat-label">家纺行业</div></div>
      <div class="stat-card"><div class="stat-num" data-target="{per_mod['retail']}">0</div><div class="stat-label">商业零售</div></div>
      <div class="stat-card"><div class="stat-num" data-target="{research_total}">0</div><div class="stat-label">行业研究</div></div>
      <div class="stat-card"><div class="stat-num" data-target="{len(quotes)}">0</div><div class="stat-label">今日金句</div></div>
    </div>
  </div>
</header>

{legend}

<main>
{chr(10).join(bodies)}
{quotes_html}
</main>

<footer>
  <div class="footer-stats">
    <span>资讯 <strong>{total}</strong> 条</span>
    <span class="sep">·</span>
    <span>家纺 {per_mod['home']} 条</span>
    <span class="sep">·</span>
    <span>商业零售 {per_mod['retail']} 条</span>
    <span class="sep">·</span>
    <span>今日金句 {len(quotes)} 句</span>
    <span class="sep">·</span>
    <span>{date} · {weekday} · 北京时间</span>
  </div>
  <div class="footer-source">数据来源：实时网页检索聚合（WebSearch）· 品牌官网 / 权威媒体 / 券商研报 · 日报日期 {date} · 内容版权归原作者所有</div>
</footer>

<script>const supportsObserver='IntersectionObserver' in window;
const sections=document.querySelectorAll('section[id]');
const navLinks=document.querySelectorAll('.topnav-links button');
function setActiveNav(id){{navLinks.forEach(b=>b.classList.toggle('active',b.dataset.target===id));}}
navLinks.forEach(button=>{{button.addEventListener('click',()=>{{const s=document.getElementById(button.dataset.target);if(!s)return;setActiveNav(s.id);try{{s.scrollIntoView({{behavior:'smooth',block:'start'}});}}catch(_){{s.scrollIntoView(true);}}}});}});
function animateNum(el,target,duration){{const start=performance.now();function tick(now){{const t=Math.min((now-start)/duration,1);const eased=1-Math.pow(1-t,3);el.textContent=Math.round(eased*target);if(t<1)requestAnimationFrame(tick);}}requestAnimationFrame(tick);}}
const statNums=document.querySelectorAll('.stat-num[data-target]');
if(supportsObserver){{const o=new IntersectionObserver((es)=>{{es.forEach(e=>{{if(e.isIntersecting){{const t=parseInt(e.target.dataset.target,10);if(!isNaN(t))animateNum(e.target,t,1200);o.unobserve(e.target);}}}});}},{{threshold:0.4}});statNums.forEach(el=>o.observe(el));}}
else{{statNums.forEach(el=>{{const t=parseInt(el.dataset.target,10);if(!isNaN(t))el.textContent=t;}});}}
const cards=document.querySelectorAll('.card,.quote-card');
if(supportsObserver){{const co=new IntersectionObserver((es)=>{{es.forEach((e,i)=>{{if(e.isIntersecting){{e.target.style.transitionDelay=(i%6)*40+'ms';e.target.classList.add('visible');co.unobserve(e.target);}}}});}},{{threshold:0.15}});cards.forEach(el=>co.observe(el));}}
else{{cards.forEach(el=>el.classList.add('visible'));}}
if(supportsObserver){{const spy=new IntersectionObserver((es)=>{{es.forEach(e=>{{if(e.isIntersecting)setActiveNav(e.target.id);}});}},{{rootMargin:'-40% 0px -55% 0px'}});sections.forEach(s=>spy.observe(s));}}
document.querySelectorAll('.module').forEach(mod=>{{
  const bf=mod.querySelectorAll('.bf');
  const mc=mod.querySelectorAll('.card');
  bf.forEach(btn=>btn.addEventListener('click',()=>{{
    const b=btn.dataset.brand;
    const active=btn.classList.contains('active');
    bf.forEach(x=>x.classList.remove('active'));
    if(active){{mc.forEach(c=>c.style.display='');return;}}
    btn.classList.add('active');
    mc.forEach(c=>{{c.style.display=(c.dataset.brand===b)?'':'none';}});
  }}));
}});
document.querySelectorAll('[data-copy]').forEach(el=>{{el.addEventListener('click',e=>{{
  if(el.tagName==='A')return;
  const txt=el.dataset.copy;
  const done=()=>{{const t=document.getElementById('toast');if(!t)return;t.textContent='链接已复制，可直接粘贴分享';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800);}};
  if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(txt).then(done).catch(done);}}else{{done();}}
}});}});</script>
<div id="toast"></div>
</body>
</html>
'''


if __name__ == "__main__":
    doc, stem = load(sys.argv[1] if len(sys.argv) > 1 else None)
    out = ROOT / "index.html"
    out.write_text(build(doc), encoding="utf-8")
    print(f"built {out}  ({out.stat().st_size/1024:.0f} KB)  from data/{stem}.json")
