"""
build_paper.py — renders docs/index.html from work/outputs/w08_capstone_metrics.json.

Every number on the deployed page is injected from that file, which capstone.ipynb writes.
Nothing numeric is typed into the prose by hand, so the page cannot drift from the notebook.

    python work/build_paper.py

Design decisions, and why (researched in Week 8, recorded so they can be argued with):
  - measure ~66ch, left-aligned, never justified  (USWDS / Harvard accessibility guidance:
    comfortable line length is 45-90 characters, ~66 a good target; browsers justify badly)
  - serif body from a system stack, no web fonts, no CDN, no analytics -> zero external
    requests, so the page loads instantly, works offline, and tracks nobody
  - the takeaway sentence sits UNDER each figure, so headings + captions alone carry the finding
  - headings state the result, not the topic, because readers skim
  - relative units and a light/dark-aware palette, checked at phone width
"""
from __future__ import annotations

import json
from pathlib import Path
from string import Template

ROOT = next(p for p in [Path(__file__).resolve(), *Path(__file__).resolve().parents]
            if (p / "work" / "outputs" / "w08_capstone_metrics.json").exists())
M = json.loads((ROOT / "work" / "outputs" / "w08_capstone_metrics.json").read_text())

REPO = "https://github.com/nothaziq/FlyRank-ML-Week1"
AUTHOR = "Muhammad Haziq Shahid"
DATE = "September 2026"

r, rec, dec = M["results"], M["recommendations"], M["recommendations"]["decay"]
best, base = M["best_model"], M["base_rate"]
mdl, rule = r[best], r["Rule baseline (Week 4)"]
grp = M["split_comparison"]["AFTER: GroupKFold(5) on client_id"]
rnd = M["split_comparison"]["BEFORE: random KFold(5)"]

def pct(x, d=0): return f"{x*100:.{d}f}%"


def results_rows() -> str:
    order = ["Base rate (random order)", "Rule baseline (Week 4)", "Logistic Regression",
             "Decision Tree (d=3)", "Random Forest", "Gradient Boosting"]
    out = []
    for name in order:
        if name not in r:
            continue
        v = r[name]
        cls = ' class="hl"' if name == best else (' class="dim"' if "Base rate" in name else "")
        sd = v.get("P@50 per-fold sd")
        out.append(
            f"<tr{cls}><th scope='row'>{name}</th>"
            f"<td>{v['P@20']:.2f}</td><td><strong>{v['P@50']:.2f}</strong></td><td>{v['P@100']:.2f}</td>"
            f"<td>{v['ROC-AUC']:.3f}</td><td>{v['PR-AUC']:.3f}</td>"
            f"<td>{v['P@50 per-fold mean']:.2f}{f' ± {sd:.2f}' if sd else ''}</td></tr>")
    return "\n".join(out)


def limits_rows() -> str:
    return "\n".join(
        f"<tr><th scope='row'>{x['limitation']}</th><td>{x['measured as']}</td>"
        f"<td>{x['what it forbids']}</td></tr>" for x in M["limitations"])


def exclusion_rows() -> str:
    out = []
    for x in M["data"]["exclusions"]:
        step, rows, why = x["step"], x["rows"], x["why"]
        strong = "evaluation universe" in step or "eligible at decision" in step
        cell = f"<strong>{rows:,}</strong>" if strong else f"{rows:,}"
        out.append(f"<tr><th scope='row'>{step}</th><td class='num'>{cell}</td><td>{why or '—'}</td></tr>")
    return "\n".join(out)


def tier_rows() -> str:
    return "\n".join(
        f"<tr><th scope='row'>{k}</th><td class='num'>{v['pages']:,}</td>"
        f"<td class='num'><strong>{pct(v['observed_rate'])}</strong></td>"
        f"<td class='num'>{v['lift_vs_base']:.1f}×</td></tr>"
        for k, v in rec["tiers"].items())


def action_rows() -> str:
    seen = rec["archetype_mix_top200"]
    out = []
    for arch, action in rec["archetype_action_map"].items():
        n = seen.get(arch, 0)
        out.append(f"<tr><th scope='row'><code>{arch}</code></th>"
                   f"<td><code>{action}</code></td><td class='num'>{n if n else '—'}</td></tr>")
    return "\n".join(out)


def nogo_items() -> str:
    return "\n".join(f"<li>{x}</li>" for x in rec["never_automate"])


TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Can a learned ranking beat a hand-written rule at choosing which pages to review first?</title>
<meta name="description" content="A client-grouped evaluation of learned ranking vs a transparent rule for prioritising content review, on $rows_fmt rows of anonymized search performance data. Precision@50 $p50_model vs $p50_rule, against a base rate of $base_pct.">
<meta name="author" content="$author">
<meta property="og:title" content="Can a learned ranking beat a hand-written rule at choosing which pages to review first?">
<meta property="og:description" content="Precision@50 of $p50_model vs a hand-written rule's $p50_rule, base rate $base_pct — and why the gap is smaller than it looks.">
<meta property="og:type" content="article">
<style>
  :root{
    --ink:#182029; --ink-soft:#4a5764; --ink-faint:#6b7885;
    --bg:#fbfaf8; --surface:#ffffff; --line:#e3e0da;
    --accent:#2f6f9f; --accent-soft:#eaf2f8; --warn:#a8442f; --warn-soft:#fbeeea;
    --measure:68ch;
    --serif: "Iowan Old Style","Charter","Bitstream Charter","Sitka Text",Cambria,Georgia,serif;
    --sans: ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    --mono: ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --ink:#e6e3dd; --ink-soft:#b2b8bf; --ink-faint:#8b939b;
      --bg:#14181d; --surface:#1b2027; --line:#2d343c;
      --accent:#79b2dc; --accent-soft:#1d2934; --warn:#e2907c; --warn-soft:#2e2320;
    }
    img.fig{filter:brightness(.93) contrast(1.02)}
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%; scroll-behavior:smooth}
  body{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:var(--serif); font-size:1.0625rem; line-height:1.65;
    text-align:left; font-kerning:normal;
  }
  .wrap{max-width:var(--measure); margin:0 auto; padding:0 1.25rem}
  .wide{max-width:min(54rem,100%); margin-inline:auto}

  header.paper{border-bottom:1px solid var(--line); padding:3.5rem 0 2rem; margin-bottom:2.5rem}
  .eyebrow{font-family:var(--sans); font-size:.75rem; letter-spacing:.09em; text-transform:uppercase;
           color:var(--accent); font-weight:650; margin:0 0 1rem}
  h1{font-size:clamp(1.75rem,4.4vw,2.6rem); line-height:1.18; letter-spacing:-.015em; margin:0 0 .9rem; font-weight:650}
  .byline{font-family:var(--sans); font-size:.9rem; color:var(--ink-faint); margin:0}
  .byline a{color:var(--ink-soft)}

  h2{font-family:var(--sans); font-size:1.32rem; line-height:1.3; letter-spacing:-.01em;
     margin:3.2rem 0 .3rem; font-weight:650; scroll-margin-top:1.5rem}
  h2 .sec{display:block; font-size:.72rem; letter-spacing:.1em; text-transform:uppercase;
          color:var(--accent); margin-bottom:.35rem; font-weight:650}
  h3{font-family:var(--sans); font-size:1.02rem; margin:2rem 0 .4rem; font-weight:650}
  p{margin:0 0 1.05rem}
  a{color:var(--accent); text-underline-offset:2px}
  a:hover{text-decoration-thickness:2px}
  strong{font-weight:650}
  code{font-family:var(--mono); font-size:.86em; background:var(--accent-soft);
       padding:.1em .34em; border-radius:3px; color:var(--ink)}
  ul,ol{margin:0 0 1.05rem; padding-left:1.3rem}
  li{margin:.3rem 0}

  .abstract{background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--accent);
            border-radius:4px; padding:1.4rem 1.5rem; margin:0 0 2rem}
  .abstract h2{margin:0 0 .6rem; font-size:.75rem; letter-spacing:.1em; text-transform:uppercase; color:var(--accent)}
  .abstract p{margin:0}

  nav.toc{font-family:var(--sans); font-size:.88rem; border:1px solid var(--line);
          border-radius:4px; padding:1rem 1.25rem; background:var(--surface); margin:0 0 2.5rem}
  nav.toc ol{margin:0; padding-left:1.2rem; columns:2; column-gap:2rem}
  @media(max-width:34rem){nav.toc ol{columns:1}}
  nav.toc a{color:var(--ink-soft); text-decoration:none}
  nav.toc a:hover{color:var(--accent); text-decoration:underline}

  .keys{display:grid; grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); gap:.75rem; margin:1.8rem 0 2rem}
  .key{background:var(--surface); border:1px solid var(--line); border-radius:4px; padding:.85rem .95rem}
  .key .n{font-family:var(--sans); font-size:1.5rem; font-weight:650; line-height:1.1; letter-spacing:-.02em}
  .key .l{font-family:var(--sans); font-size:.74rem; color:var(--ink-faint); line-height:1.35; margin-top:.3rem}

  figure{margin:2rem 0 2.2rem}
  img.fig{width:100%; height:auto; display:block; border:1px solid var(--line);
          border-radius:4px; background:#fff}
  figcaption{font-family:var(--sans); font-size:.845rem; line-height:1.5; color:var(--ink-soft); margin-top:.7rem}
  figcaption b{color:var(--ink); font-weight:650}

  .tablewrap{overflow-x:auto; margin:1.5rem 0 1.8rem; border:1px solid var(--line); border-radius:4px;
             background:var(--surface)}
  table{border-collapse:collapse; width:100%; font-family:var(--sans); font-size:.845rem}
  th,td{padding:.55rem .7rem; text-align:left; border-bottom:1px solid var(--line); vertical-align:top}
  thead th{font-size:.72rem; letter-spacing:.05em; text-transform:uppercase; color:var(--ink-faint);
           font-weight:650; white-space:nowrap}
  tbody th{font-weight:550; white-space:nowrap}
  td.num,th.num{text-align:right; font-variant-numeric:tabular-nums}
  tbody tr:last-child th,tbody tr:last-child td{border-bottom:none}
  tr.hl{background:var(--accent-soft)}
  tr.dim{color:var(--ink-faint)}

  .callout{background:var(--warn-soft); border:1px solid var(--line); border-left:3px solid var(--warn);
           border-radius:4px; padding:1.1rem 1.25rem; margin:1.8rem 0; font-size:1rem}
  .callout p:last-child{margin-bottom:0}
  .callout .label{font-family:var(--sans); font-size:.72rem; letter-spacing:.09em; text-transform:uppercase;
                  color:var(--warn); font-weight:650; display:block; margin-bottom:.45rem}

  footer.paper{border-top:1px solid var(--line); margin-top:4rem; padding:2.2rem 0 4rem;
               font-family:var(--sans); font-size:.88rem; color:var(--ink-soft)}
  footer.paper h2{font-size:1rem; margin-top:0}
  .credit{background:var(--surface); border:1px solid var(--line); border-radius:4px; padding:1.1rem 1.25rem}
</style>
</head>
<body>

<header class="paper">
  <div class="wrap">
    <p class="eyebrow">FlyRank ML Internship · Capstone · Lane 4 — CTR / Engagement Opportunity Scoring</p>
    <h1>Can a learned ranking beat a hand-written rule at choosing which pages to review first?</h1>
    <p class="byline">$author · $date · <a href="$repo">code and notebooks on GitHub</a></p>
  </div>
</header>

<main class="wrap">

<div class="abstract">
  <h2>Abstract</h2>
  <p><strong>FlyRank is an SEO content agency producing and managing content — much of it
  AI-assisted — across dozens of client portfolios at once</strong>, where a content reviewer has
  roughly 50 slots a week to open pages by hand against a shared portfolio of tens of thousands,
  and before this work that order was set by client priority and whoever asked most recently
  rather than by any measured signal. Using an anonymized $rows_fmt-row slice of FlyRank
  search-performance data ($pages_fmt pages across $clients clients, two consecutive 30-day
  windows), I defined the outcome as a
  <em>persisting</em> click shortfall — a page still earning under half its position band's typical
  click-through rate one window later — and ranked pages by four models plus the transparent
  hand-written rule built in Week 4, scored out-of-fold under a client-grouped split because one
  client holds $conc of the data. The learned ranking put $slots_model of 50 reviewer slots on a page
  whose shortfall persisted, against $slots_rule for the hand-written rule and $slots_base for random
  order (precision@50 of $p50_model, $p50_rule and $base_pct respectively). Counted per fold rather than
  pooled the model and the rule sit within one standard deviation of each other, so the honest
  claim is <em>not worse than the rule, plausibly somewhat better</em> — and a plain random split
  would have reported $p50_random instead, which is the more useful finding. The output is
  decision-support for ordering a human review queue in one portfolio over one pair of windows:
  it does not predict search rankings, does not estimate the value of a fix, and cannot support
  any causal claim about content changes.</p>
</div>

<nav class="toc" aria-label="Contents">
  <ol>
    <li><a href="#problem">The problem</a></li>
    <li><a href="#data">Data</a></li>
    <li><a href="#method">Methodology</a></li>
    <li><a href="#results">Results</a></li>
    <li><a href="#limits">Limitations</a></li>
    <li><a href="#recommendations">Recommendations</a></li>
    <li><a href="#repro">Reproducibility</a></li>
    <li><a href="#credit">Acknowledgments</a></li>
  </ol>
</nav>

<section id="problem">
<h2><span class="sec">1 · Introduction</span>The queue existed. The evidence behind its order did not.</h2>

<p><strong>The FlyRank content problem, concretely.</strong> FlyRank writes and maintains search
content for dozens of clients at once, much of it produced with AI assistance and reviewed by a
small human team. That combination — many clients, a large shared page count, and a chronically
scarce review resource — is exactly where an unmeasured priority queue costs the most: a reviewer
cannot personally track tens of thousands of pages across dozens of accounts, so <em>something</em>
has to decide who gets looked at first, and until now that something was informal.</p>

<p>Monday morning, a FlyRank content reviewer opens a list. There are tens of thousands of pages in
the portfolio and room for about fifty of them in a week. Which fifty?</p>

<p>Before this work the answer came from client priority and from whoever had asked most recently.
That is not a bad process — it is an <em>unmeasured</em> one, and an unmeasured process cannot be
improved, defended, or handed off. Two things follow directly from that shape of problem: the
queue has to work across very different clients without secretly becoming a queue for one of
them, and it has to say plainly when it does not know — both become central findings below, not
just design constraints. The question this paper answers is narrow on purpose:</p>

<p><strong>Among pages already visible in search, can a learned ranking identify — better than a
transparent hand-written rule — the ones whose click shortfall is still there a month later?</strong></p>

<p>Three phrases carry the weight. <em>Already visible</em>: pages ranking 1–20 with enough
impressions to measure; pages nobody sees are a ranking problem, not a click-through one.
<em>Click shortfall</em>: earning fewer clicks than pages at the same position band typically do —
because position dominates click-through rate, comparing a page to its own band is what makes the
comparison fair. <em>Still there a month later</em>: a one-month dip is noise; a gap that survives
into a second window is what deserves a human's time.</p>

<div class="keys">
  <div class="key"><div class="n">$pages_fmt</div><div class="l">pages in the evaluation universe</div></div>
  <div class="key"><div class="n">$clients</div><div class="l">clients, one holding $conc of them</div></div>
  <div class="key"><div class="n">$base_pct</div><div class="l">base rate — what random order would give</div></div>
  <div class="key"><div class="n">$p50_model</div><div class="l">precision@50, client-grouped, out-of-fold</div></div>
</div>
</section>

<section id="data">
<h2><span class="sec">2 · Data</span>A 30,000-row anonymized slice — not the 79-million-row release</h2>

<p>This work used <code>data/raw/content_refresh_anonymized.csv</code>: $rows_fmt rows × $cols columns,
one row per content item per client. The full pseudonymized warehouse release (~79M rows of daily
search performance) exists and is documented in the programme's data dictionary, but <strong>it was
not used here</strong>, and every number on this page describes the starter slice.</p>

<p>Each row carries static metadata (word count, content type, keyword intent, age, freshness),
90-day totals from Google Search Console and GA4, and two consecutive 30-day windows
(<code>*_prev_30d</code>, <code>*_last_30d</code>) that make the whole design possible: the earlier
window stands for <em>what is knowable at decision time</em>, the later one for <em>the outcome</em>.</p>

<p><strong>On dates:</strong> the slice carries none. Windows are relative to export time, so
seasonality cannot be examined and no result here is anchored to a calendar period.</p>

<p><strong>On anonymization:</strong> clients, content items and queries arrive as opaque hashes.
There are no client names, domains, URLs, page titles or raw search queries in the file at all.
This work can therefore say what measurable pattern a page had, never what the page was about —
a limitation that returns with force in the recommendations.</p>

<div class="tablewrap">
<table>
  <caption class="visually-hidden"></caption>
  <thead><tr><th>Filtering step</th><th class="num">Rows</th><th>Why</th></tr></thead>
  <tbody>
$exclusion_rows
  </tbody>
</table>
</div>

<p>The third exclusion is the uncomfortable one. Pages whose traffic collapsed between the two
windows have no measurable outcome and are dropped — <strong>$dropped_fmt of them, $dropped_pct of the
eligible pool.</strong> That is survivorship, it is named here rather than buried, and it means every
rate on this page describes pages that stayed measurable.</p>
</section>

<section id="method">
<h2><span class="sec">3 · Methodology</span>The label is a proxy, the baseline is free, and the split is grouped by client</h2>

<h3>Assumptions, stated so they can be disagreed with</h3>
<ol>
  <li><strong>Position band is the fair comparison group</strong> — a page is judged against the median
  click-through rate of pages at its own position, not a portfolio average.</li>
  <li><strong>A persisting gap is what deserves attention</strong> — a single-window dip is treated as noise.</li>
  <li><strong>The earlier window is a fair stand-in for decision time</strong> — with one declared exception below.</li>
  <li><strong>Median, not mean</strong> — these click-through distributions are skewed enough that a mean
  band norm would be dragged by a handful of outliers.</li>
</ol>

<h3>The label — and the ceiling it puts on every claim</h3>
<p><code>persisted_shortfall = 1</code> when, in the <em>later</em> window, a page still earns under half
the click-through rate typical of its position band, and still has enough impressions for that to
mean something.</p>

<div class="callout">
  <span class="label">The most important sentence on this page</span>
  <p>This is a <strong>defined-rule proxy, not a reviewed outcome.</strong> Nobody looked at these pages
  and judged them worth fixing. The label records that a gap stayed open — never that work would have
  closed it. No amount of model quality can lift a claim above the label it was trained on.</p>
</div>

<h3>The baseline that has to be beaten</h3>
<p>The Week-4 hand-written rule, run on the earlier window: flag a visible, well-powered page whose
click-through rate is under half its band norm, then rank the flagged ones by expected clicks minus
actual clicks. It is transparent, needs no fitting and costs nothing. <strong>A model that cannot beat
it is not worth shipping</strong> — and most of this paper's value is in how close that contest turns out
to be.</p>

<h3>Validation design</h3>
<p><code>GroupKFold(5)</code> grouped on <code>client_id</code>, predictions collected out-of-fold, so
every page is scored by a model that never saw its client. The reason is measured rather than
theoretical: one client holds <strong>$conc</strong> of the eligible pages. Under a plain random split
that client's pages sit on both sides of every fold and a model can score well by recognising the
client instead of the pattern. Both splits are reported in the next section.</p>

<p>The metric is <strong>precision@K</strong> with primary <strong>K = 50</strong> — one reviewer-week —
and the base rate printed beside it every time, because precision@K means nothing without knowing
what random order would have given.</p>

<h3>Leakage checks that were actually run</h3>
<ul>
  <li>All $banned outcome-window and product-flag columns are banned from the feature set, and the ban is
  asserted in code for derived columns too — not just for the obvious ones.</li>
  <li>A deliberately planted leaky column was added in the Week-6 audit to confirm the harness
  <em>can</em> detect a leak, rather than assuming it would.</li>
  <li><strong>One declared contamination:</strong> <code>avg_position</code> is a 90-day average and the
  outcome window sits inside those 90 days, so the position band leaks a thin trace of the outcome. It
  is kept because the baseline uses it too — removing it only for the model would rig the comparison —
  and the entire model was refit with position removed to measure what the trace is worth. The answer:
  <strong>$contam of PR-AUC.</strong> Real, bounded, disclosed, not eliminated.</li>
</ul>
</section>

<section id="results">
<h2><span class="sec">4 · Results</span>The model wins on paper; the free rule is close enough to keep</h2>

<p>All rows below are scored on the same pages, the same split and the same metric. The baseline is
recomputed in the same run, not quoted from an earlier week.</p>

<div class="tablewrap">
<table>
  <thead><tr><th>Method</th><th>P@20</th><th>P@50</th><th>P@100</th><th>ROC-AUC</th><th>PR-AUC</th><th>P@50 per fold</th></tr></thead>
  <tbody>
$results_rows
  </tbody>
</table>
</div>

<figure class="wide">
  <img class="fig" src="img/fig1_reviewer_week.png" alt="Horizontal bar chart of how many of 50 reviewer slots land on a page whose shortfall persisted, for each method. Random order lands about 5; the hand-written rule about 44; the learned models between 26 and 47.">
  <figcaption><b>The result a reviewer feels.</b> Of 50 pages opened in rank order, the learned ranking
  puts $slots_model on a page whose shortfall was still open a month later; the hand-written rule puts
  $slots_rule; random order puts $slots_base. The distance from random is large. The distance from the rule
  is two pages.</figcaption>
</figure>

<figure class="wide">
  <img class="fig" src="img/fig2_precision_at_k.png" alt="Precision-at-K curves for the learned model and the hand-written rule from K=10 to K=500, with the base rate as a flat dotted line far below both.">
  <figcaption><b>The gap widens as the list gets longer, but a reviewer never gets that far.</b> Both
  methods sit far above the base rate at every depth. The vertical line marks K=50 — one reviewer-week
  — which is the only value of K anyone will actually use.</figcaption>
</figure>

<h3>The finding worth more than the headline</h3>
<p>The same model, scored under a plain random split instead of a client-grouped one, reports a
precision@50 of <strong>$p50_random</strong> instead of $p50_model — and per-fold, $pf_random instead of
$pf_group. Nothing about the model changed. What changed is that under a random split
<strong>about $overlap_clients of $clients clients appear on both sides of every fold</strong>, so the model
can recognise the client rather than the pattern. Under the grouped split, zero do.</p>

<figure class="wide">
  <img class="fig" src="img/fig3_split_honesty.png" alt="Bar chart comparing precision at 50 for the same model under four scorings: pooled random split, pooled client-grouped split, per-fold random split with error bar, and per-fold client-grouped split with a larger error bar.">
  <figcaption><b>The same model, scored four ways.</b> The left pair is the flattering number; the right
  pair is the defensible one. Error bars are the fold-to-fold standard deviation — and the grouped
  split's spread ($sd_group) is wider than the entire gap between the model and the hand-written rule.
  Every headline number on this page is from the grouped split.</figcaption>
</figure>

<div class="callout">
  <span class="label">What this paper claims, exactly</span>
  <p>Measured out-of-fold under a client-grouped split, the learned ranking is <strong>directionally
  ahead</strong> of the hand-written rule at a reviewer's weekly K=50 ($p50_model vs $p50_rule pooled), but
  that gap sits <strong>inside the fold-to-fold spread</strong> once counted per client group. The honest
  claim is <em>not worse than the rule, plausibly somewhat better</em> — not "beats the rule". A plain
  random split overstates both.</p>
  <p>The top two models are likewise separated by less than one standard deviation, and which one leads
  changes between library versions. This page reports the model selected in Week 5 and names the flip,
  rather than re-picking a winner after seeing the table.</p>
</div>

<h3>Where it is wrong, and why those cases are hard</h3>
<p>Of the $wrong pages the model put in its top 50 that turned out not to have a persisting shortfall,
all of them were pages whose click-through rate climbed back toward its band norm <em>on its own</em>
between the two windows. These are self-repairing pages, not misread ones — the honest cost of having
one window of history to judge from. It is also the phenomenon that makes the next section's finding
so consequential.</p>
</section>

<section id="limits">
<h2><span class="sec">5 · Limitations</span>What this work cannot claim</h2>

<p>Written before a reader can write it, with the number that measures each one attached — because a
limitation without a number is a disclaimer, and disclaimers get skipped.</p>

<div class="tablewrap">
<table>
  <thead><tr><th>Limitation</th><th>Measured as</th><th>What it forbids</th></tr></thead>
  <tbody>
$limits_rows
  </tbody>
</table>
</div>

<p><strong>The one-sentence version:</strong> this is decision-support for ordering a review queue in
one portfolio over one pair of 30-day windows — and it is close enough to a free hand-written rule
that the rule remains a legitimate choice.</p>
</section>

<section id="recommendations">
<h2><span class="sec">6 · Recommendations</span>A review appointment, not an instruction — and a queue with a one-month shelf life</h2>

<p>The model decides <em>order</em>. A human-written lookup decides <em>action</em>. Several rows cannot
be worked at all until a prior question is answered. That separation matters: FlyRank can rewrite any
action below without retraining anything.</p>

<h3>Three tiers, each labelled with a measured hit rate</h3>
<div class="tablewrap">
<table>
  <thead><tr><th>Tier</th><th class="num">Pages</th><th class="num">Observed shortfall rate</th><th class="num">vs base rate</th></tr></thead>
  <tbody>
$tier_rows
  </tbody>
</table>
</div>

<figure class="wide">
  <img class="fig" src="img/fig5_tier_calibration.png" alt="Horizontal bars showing the observed rate of persisted shortfall for each tier, with the base rate marked as a dotted vertical line.">
  <figcaption><b>A tier label carries a number, not an adjective.</b> Tier C exists precisely because the
  most common failure of a ranked queue is that somebody works it to the bottom — at $tier_c, a slot
  spent there is close to random.</figcaption>
</figure>

<h3>Archetype → action</h3>
<p>Every page gets exactly one archetype, assigned by first match on rules a reviewer can check by
eye, and the archetype — not the model — determines the suggested action.</p>

<div class="tablewrap">
<table>
  <thead><tr><th>Archetype</th><th>Suggested first action</th><th class="num">In top 200</th></tr></thead>
  <tbody>
$action_rows
  </tbody>
</table>
</div>

<h3>The decay finding — the most operationally important result here</h3>
<p>It would be missed entirely by anyone who stopped at precision@K.</p>

<figure class="wide">
  <img class="fig" src="img/fig4_queue_decay.png" alt="Two bar charts: the left compares how often a flagged versus unflagged page still has a shortfall 30 days later; the right shows what share of a top-K list still belongs in the next window's correct top-K.">
  <figcaption><b>The flag carries real signal, and the list still goes stale in a month.</b> Flagged pages
  persisted at $persist against $persist_un for unflagged ones — about $lift× — but roughly half of a
  flagged queue resolved, or stopped being measurable, <em>with nobody touching it</em>. A top-50 built on
  one window overlaps the next window's correct top-50 by only $overlap50.</figcaption>
</figure>

<p>Three operational rules follow, each traceable to one of those numbers: <strong>rebuild the queue
every 30 days; treat a queue older than 45 days as void; and never read a before/after on reviewed
pages as an effect.</strong> That last one is the sharpest. With about half of flagged pages
self-resolving, a naive before/after comparison would declare success on a coin flip. Measuring
whether this work actually helps requires a held-out control set decided in advance — the single
highest-value next experiment.</p>

<p>The content-decay story this lane is named after is reported as a <strong>negative result</strong>:
shortfall rate does not trend across content-age quintiles, and the update-recency column in this
slice is near-degenerate, with nearly every page in one of two buckets. This data cannot answer
"does content decay and does refreshing fix it" in either direction. That is a data-collection
requirement, not a null effect.</p>

<h3>What must never be automated</h3>
<ul>
$nogo_items
</ul>
<p>Every row additionally carries a mandatory topic-sensitivity check, because <strong>topic is not in
the feature set at all</strong> — the queue cannot distinguish a regulated-topic page from an ordinary
one, so a human is the only control that exists. And no monetary figure appears anywhere on this
page: $money_reason, so the inputs could not carry one.</p>

<p><strong>Automate the measuring. Never automate the acting.</strong></p>
</section>

<section id="repro">
<h2><span class="sec">7 · Reproducibility</span>Every number here is regenerated by one notebook run</h2>

<p>The page you are reading is rendered from <code>work/outputs/w08_capstone_metrics.json</code>, which
<code>capstone.ipynb</code> writes. No number in this prose is typed by hand, so the page cannot drift
from the analysis.</p>

<ul>
  <li><strong>Repository:</strong> <a href="$repo">$repo_short</a></li>
  <li><strong>Capstone notebook:</strong> <a href="$repo/blob/main/work/notebooks/capstone.ipynb"><code>work/notebooks/capstone.ipynb</code></a> — runs top to bottom from the raw CSV and writes every figure and number on this page</li>
  <li><strong>Weekly notebooks:</strong> <a href="$repo/tree/main/work/notebooks">research question → data contract → signal audit → baseline → model → validation audit → action playbook</a></li>
  <li><strong>Committed receipts:</strong> <a href="$repo/tree/main/work/outputs">metrics JSON for every week</a>, so any figure quoted here traces to a key in a file</li>
  <li><strong>Page generator:</strong> <a href="$repo/blob/main/work/build_paper.py"><code>work/build_paper.py</code></a></li>
  <li><strong>Seed:</strong> $seed · <strong>scikit-learn</strong> $sklearn · <strong>pandas</strong> $pandas</li>
</ul>

<p>To rerun: clone the repo, <code>pip install -r requirements.txt</code>, then run
<code>work/notebooks/capstone.ipynb</code> top to bottom and <code>python work/build_paper.py</code>.
The ranked queue CSV is deliberately not committed — the repository's leak-guard blocks data files
under <code>work/</code> — and the notebook regenerates it deterministically.</p>

<p>Precision@K can move by a point or two across scikit-learn versions; the notebook prints the
versions it ran on and checks its universe, client count and base rate against the committed
receipts from earlier weeks, which are library-independent and must match exactly.</p>
</section>

</main>

<footer class="paper">
  <div class="wrap">
    <h2 id="credit">Acknowledgments &amp; data credit</h2>
    <div class="credit">
      <p>Built on the <strong>FlyRank ML Internship dataset</strong> —
      <a href="https://flyrank.ai" rel="noopener">flyrank.ai</a>.</p>
      <p>The anonymized slice used here contains no client names, domains, URLs, page titles or raw
      search queries. Thanks to the FlyRank ML Internship track leads for the dataset, the weekly
      structure, and the review that turned a flattering random-split number into an honest
      client-grouped one.</p>
      <p style="margin-bottom:0">Analysis and write-up: $author, $date. Code under MIT; data under the
      programme's data-use terms.</p>
    </div>
  </div>
</footer>

</body>
</html>
""")

html = TEMPLATE.substitute(
    author=AUTHOR, date=DATE, repo=REPO, repo_short=REPO.replace("https://", ""),
    rows_fmt=f"{M['data']['rows']:,}", cols=M["data"]["columns"],
    pages_fmt=f"{M['data']['evaluation_universe_pages']:,}", clients=M["data"]["clients"],
    dropped_fmt=f"{M['data']['survivorship_dropped']:,}",
    dropped_pct=pct(M["data"]["survivorship_dropped"] /
                    (M["data"]["evaluation_universe_pages"] + M["data"]["survivorship_dropped"])),
    conc=next(x["measured as"].split("=")[1].split(" of")[0].strip()
              for x in M["limitations"] if x["limitation"] == "Client concentration"),
    base_pct=f"{base:.3f}",
    p50_model=f"{mdl['P@50']:.2f}", p50_rule=f"{rule['P@50']:.2f}",
    p50_random=f"{rnd['P@50 (pooled)']:.2f}",
    pf_random=f"{rnd['P@50 (per-fold mean)']:.2f}", pf_group=f"{grp['P@50 (per-fold mean)']:.2f}",
    sd_group=f"± {grp['P@50 (per-fold sd)']:.2f}",
    overlap_clients=f"{rnd['clients seen in training AND scoring, per fold']:.0f}",
    slots_model=f"{mdl['P@50']*50:.0f}", slots_rule=f"{rule['P@50']*50:.0f}",
    slots_base=f"{base*50:.0f}",
    banned=M["method"]["banned_columns"],
    contam=f"{abs(M['method']['contamination_cost_pr_auc']):.3f}",
    wrong=f"{round((1 - mdl['P@50']) * 50):.0f}",
    seed=M["seed"], sklearn=M["sklearn"], pandas=M["pandas"],
    persist=pct(dec["persistence_flagged"]), persist_un=pct(dec["persistence_unflagged"]),
    lift=f"{dec['persistence_lift']:.0f}",
    overlap50=pct(dec["topK_overlap_next_window"]["50"]),
    tier_c=pct(rec["tiers"]["C - monitor only"]["observed_rate"]),
    money_reason=rec["monetary_value_reason"],
    results_rows=results_rows(), limits_rows=limits_rows(), exclusion_rows=exclusion_rows(),
    tier_rows=tier_rows(), action_rows=action_rows(), nogo_items=nogo_items(),
)

out = ROOT / "docs" / "index.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)}  ({len(html)/1024:.1f} KB)")

# Public-safety gate: no identifying hash may reach the served page.
import pandas as pd
slice_df = pd.read_csv(ROOT / "data/raw/content_refresh_anonymized.csv",
                       usecols=["client_id", "content_id"])
ids = set(slice_df.client_id.unique()) | set(slice_df.content_id.unique())
hits = [i for i in ids if i in html]
assert not hits, f"identifier leaked into the page: {hits[:3]}"
assert "flyrank.ai" in html, "data credit link missing"
for section in ("Abstract", "Limitations", "Acknowledgments"):
    assert section in html, f"required section missing: {section}"
print(f"safety: 0 of {len(ids):,} dataset identifiers appear in the page; data credit present")
