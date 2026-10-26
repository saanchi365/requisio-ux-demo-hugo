"""Get the handbook data from the main project and prepare it for this website.

1. Downloads handbook-data.json, which the main project (requisio-ux-demo) publishes on every update.
2. Adds the sample wireframes kept in this copy (sample-wireframes/), so the Wireframes tab has something to show.
3. Works out what both websites need: overdue, wireframe order (same as the flowchart), groups by stage.
4. Writes the result to the file given as the first argument, and copies wireframe pictures to the folder
   given as the second argument.

Usage: python scripts/prepare_data.py <output.json> <static-wireframes-folder>
"""
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = os.environ.get("HANDBOOK_DATA_URL", "https://saanchi365.github.io/requisio-ux-demo/handbook-data.json")
out_json, out_pics = Path(sys.argv[1]), Path(sys.argv[2])
sys.stdout.reconfigure(encoding="utf-8")

data = json.load(urllib.request.urlopen(f"{SOURCE}?t={datetime.now().timestamp():.0f}"))
today = date.today()

# ---- sample wireframes kept in this copy (the main project's own wireframes come first)
shutil.rmtree(out_pics, ignore_errors=True)
out_pics.mkdir(parents=True, exist_ok=True)
for w in data["wireframes"]:
    w["src"] = data["site"] + "wireframes/" + w["file"]
    w["sample"] = False
samples = ROOT / "sample-wireframes"
for pic in sorted(samples.glob("*.svg")) if samples.exists() else []:
    m = re.match(r"^(\d+)[-_ ]+(.*)\.svg$", pic.name)
    if not m:
        continue
    notes = pic.with_suffix(".md")
    text = notes.read_text(encoding="utf-8") if notes.exists() else ""
    desc = re.search(r"^## Description\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    qs = re.search(r"^## Open questions\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    shutil.copy(pic, out_pics / pic.name)
    data["wireframes"].append(dict(file=pic.name, n=int(m.group(1)), title=m.group(2).replace("-", " ").capitalize(),
                                   description=desc.group(1).strip() if desc else "",
                                   questions=[re.sub(r"^[-*]\s+", "", l).strip() for l in (qs.group(1) if qs else "").splitlines() if l.strip().startswith(("-", "*"))],
                                   src="wireframes/" + pic.name, sample=True))

REQ = {r["n"]: r for r in data["requirements"]}
FEAT = {f["n"]: f for f in data["features"]}
data["wireframes"] = [w for w in data["wireframes"] if w["n"] in REQ or w["n"] in FEAT]


# ---- status: overdue and due soon are worked out from today's date
def when(d):
    return date.fromisoformat(d[:10]) if d else None


data.setdefault("orphans", [])
for r in data["requirements"] + data["features"] + data["orphans"]:
    t = when(r.get("target"))
    if r["status"] != "Done" and t and t < today:
        r["status"] = "Overdue"
    r["due_soon"] = bool(r["status"] not in ("Done", "Overdue") and t and (t - today).days <= 7)
    r["target_text"] = f"{t.day} {t:%b}" if t else ""

# ---- wireframe order follows the flowchart: the box with "#7" decides where screen #7 goes
for f in data["features"]:
    order = []
    for fc in data["flowcharts"]:
        if fc["feature"] == f["n"]:
            for s in fc["steps"]:
                order += [n for n in s["refs"] if n not in order]
    mine = [w for w in data["wireframes"] if (REQ.get(w["n"], {}).get("feature") == f["n"]) or w["n"] == f["n"]]
    def place(w):
        n = w["n"]
        if n in order:
            return (order.index(n), 0, n)
        parent = REQ.get(n, {}).get("parent")  # a sub-requirement's screen sits where its requirement is
        return (order.index(parent), 1, n) if parent in order else (999, 0, n)
    mine.sort(key=lambda w: (place(w), w["file"]))
    f["wireframes"] = [w["file"] for w in mine]
    f["flowcharts"] = [fc["id"] for fc in data["flowcharts"] if fc["feature"] == f["n"]]
    f["stage"] = f["stage"] if f["stage"] in data["stages"] else "No stage chosen"
    f["slug"] = f"feature-{f['n']}"
data["stage_groups"] = [dict(stage=s, features=[f["n"] for f in data["features"] if f["stage"] == s])
                        for s in data["stages"] + ["No stage chosen"] if any(f["stage"] == s for f in data["features"])]

# ---- summaries both websites only have to display
STATUSES = ["Done", "In progress", "Overdue", "To do"]
comments_on = {}
for c in data["comments"]:
    comments_on.setdefault(c["issue"], []).append(c)
for r in data["requirements"] + data["orphans"]:
    r["comment_count"] = len(comments_on.get(r["n"], []))
    r["wireframe"] = next((w["file"] for w in data["wireframes"] if w["n"] == r["n"]), "")


def summary(reqs):
    s = {k: sum(1 for r in reqs if r["status"] == k) for k in STATUSES}
    s.update(total=len(reqs), due_soon=sum(1 for r in reqs if r["due_soon"]))
    s["pct"] = {k: round(100 * s[k] / s["total"], 1) if s["total"] else 0 for k in STATUSES}
    return s


def soonest(reqs):
    return [r["n"] for r in sorted(reqs, key=lambda r: (r["status"] == "Done", r.get("target") or "9999"))]


ordered = [n for g in data["stage_groups"] for n in g["features"]]
data["feature_order"] = ordered
data["flow_order"] = ["all"] + [n for n in ordered if FEAT[n]["flowcharts"]]
for f in data["features"]:
    reqs = [r for r in data["requirements"] if r["feature"] == f["n"]]
    f["requirement_list"] = [r["n"] for r in reqs]
    f["summary"], f["soonest"] = summary(reqs), soonest(reqs)
    issues = {f["n"], *f["requirement_list"]}
    f["comment_list"] = [i for i, c in enumerate(data["comments"]) if c["issue"] in issues]
    f["recent"] = [x for x in data["recent"] if x["feature"] == f["n"]]
    f["all_questions"] = [dict(q=q, n=None) for q in f["questions"]] + [dict(q=q, n=r["n"]) for r in reqs for q in r["questions"]]
data["summary"], data["soonest"] = summary(data["requirements"]), soonest(data["requirements"])
data["all_questions"] = [dict(q=q, n=None, feature=f["n"]) for f in data["features"] for q in f["questions"]] + \
                        [dict(q=q, n=r["n"], feature=r["feature"]) for r in data["requirements"] for q in r["questions"]]
for fc in data["flowcharts"]:
    fc["github"] = f"https://github.com/{data['repo']}/blob/main/{fc['file']}"
    for k in ("created", "updated"):
        d = when(fc.get(k))
        fc[k + "_text"] = f"{d.day} {d:%b %Y}" if d else ""
for c in data["comments"]:
    d = when(c["created"])
    c["when"] = f"{d.day} {d:%b %Y}"
for x in data["recent"]:
    d = when(x["updated"])
    x["when"] = "Today" if d == today else f"{d.day} {d:%b}"
data["req_feature"] = {str(r["n"]): r["feature"] for r in data["requirements"]}
data["prepared"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(f"Prepared {len(data['features'])} features, {len(data['requirements'])} requirements, "
      f"{len(data['flowcharts'])} flowcharts, {len(data['wireframes'])} wireframes")
