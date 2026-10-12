"""Update the static People page from normalized member data.

Run: python scripts/build_people.py
Import a new collection: python scripts/build_people.py --import-raw
Raw workbooks/photos are read-only; normalized originals retain their bytes.
Requires Pillow only for generating the small website portraits.
"""

import argparse
from calendar import month_name
from collections import Counter
import hashlib
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ROOT / "people"
PHOTOS = PEOPLE / "photo"
PORTRAITS = PEOPLE / "portraits"
RAW = PEOPLE / "raw"
DATA = PEOPLE / "members.json"
ADDITIONS = PEOPLE / "additions.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
START = "    <!-- PEOPLE DATA START -->"
END = "    <!-- PEOPLE DATA END -->"

# Editorial normalization of the supplied research text; no new topics added.
RESEARCH_TEXT = {
    "Humanoid Whole-body Manipulation": "Humanoid whole-body manipulation",
    "Manipulation, RL, embodied ai": "Manipulation, RL, embodied AI",
    "Locomotion, Safety, Reinforcement Learning": "Locomotion, safety, reinforcement learning",
    "Navigation, manipulation": "Navigation, manipulation",
    "Dexterous Manipulation; Robotics": "Dexterous manipulation, robotics",
    "Swarm robotics, multi-robot systems, robotics and autonomous systems, distributed control": "Swarm robotics, multi-robot systems, robotics and autonomous systems, distributed control",
    "Tactile sensing, Contact modeling, Manipulation": "Tactile sensing, contact modeling, manipulation",
    "Robot Learning, Reinforcement Learning, Robot Manipulation": "Robot learning, reinforcement learning, robot manipulation",
    "Robot navigation, robotic photography, robot learning": "Robot navigation, robotic photography, robot learning",
    "Manipulation，Imitation learning": "Manipulation, imitation learning",
    "Long horizon manipulation": "Long-horizon manipulation",
    "Bionic snake robot, embodied intelligence, computer vision, reinforcement learning": "Bionic snake robots, embodied intelligence, computer vision, reinforcement learning",
    "Visual tracking": "Visual tracking",
    "Deformable object manipulation, Dexterous manipulation, Agentic Robotics": "Deformable object manipulation, dexterous manipulation, agentic robotics",
    "Mobile Manipulation, Agentic Robotic": "Mobile manipulation, agentic robotics",
    "Robot Task and Motion Planning": "Robot task and motion planning",
    "机器人运动规划与场景理解": "Robot motion planning and scene understanding",
    "Bimanual Manipulation": "Bimanual manipulation",
    "Imitation learning, Bimanual manipulation": "Imitation learning, bimanual manipulation",
    "reinforcement learning, imitation learning": "Reinforcement learning, imitation learning",
    "Active Reconstruction, Aerial System: Perception and Autonomy": "Active reconstruction, aerial systems: perception and autonomy",
    "Human-robot interaction, Manipulation": "Human-robot interaction, manipulation",
    "Fabric-manipulation": "Fabric manipulation",
    "Embodied AI,  UAV，navigation": "Embodied AI, UAVs, navigation",
    "大模型智能体持续学习与自进化，具身智能体": "Continual learning and self-evolution of large-model agents, embodied agents",
    "Dexterous manipulation, Dexterous hand designing": "Dexterous manipulation, dexterous hand design",
    "Robot Learning, Dexterous Manipulation, Mobile Manipulation, Event-based Vision": "Robot learning, dexterous manipulation, mobile manipulation, event-based vision",
    "Human-Robot Interaction, Collision avoidance, Teleoperation": "Human-robot interaction, collision avoidance, teleoperation",
    "Loco-manipulation, Human-robot Interaction, RL": "Loco-manipulation, human-robot interaction, RL",
    "Loco-manipulation; Humanoid control; RL;": "Loco-manipulation, humanoid control, RL",
    "quadruped robot;navigation": "Quadruped robots, navigation",
    "Navigation, Manipulation, Human-Robot Interaction": "Navigation, manipulation, human-robot interaction",
    "SLAM, 3D Reconstruction, Building Information Model, Robot navigation": "SLAM, 3D reconstruction, building information models, robot navigation",
    "Computational Neurmorphic Vision / Large Behavior Model": "Computational neuromorphic vision, large behavior models",
    "Robotics, Reinforcement Learning": "Robotics, reinforcement learning",
    "Robotics Data Mining, Automatic Annotation System, Human-Computer Interaction": "Robotics data mining, automatic annotation systems, human-computer interaction",
}
DESTINATIONS = {
    "深圳大学助理教授": "Assistant Professor, Shenzhen University",
    "Great bay university (GBU)": "Great Bay University (GBU)",
    "京东科技 JDT，Robotics Researcher": "Robotics Researcher, JD Technology (JDT)",
    "东北林业大学": "Northeast Forestry University",
    "自主创业": "Entrepreneurship",
    "具身领域创业": "Entrepreneurship in embodied AI",
    "南方科技大学统计与数据科学系助理教授": "Assistant Professor, Department of Statistics and Data Science, Southern University of Science and Technology",
}
# Exceptions to the collection's family-name-first convention.
# Yizhou Chen is already given-name-first (https://jinxer000.github.io/).
NAME_OVERRIDES = {"郭骏德": "Junde Guo", "Yizhou Chen": "Yizhou Chen"}
# User-supplied replacement photos in people/raw take precedence over the form.
PHOTO_OVERRIDES = {"Zhengjie Shu": "zhengjieshu.jpg"}
# Reviewed square crops. Keep space above the head in tall portrait originals.
CROP_CENTERS = {
    "Zhanteng Xie": (0.5, 0.1),
    "Tengye Xu": (0.5, 0.0),
    "Shuai Zhang": (0.5, 0.0),
    "Chang Chen": (0.5, 0.0),
    "Haobo Zuo": (0.5, 0.0),
    "Yuhan Xie": (0.5, 0.0),
    "Jiaming Qi": (0.5, 0.0),
    "Junde Guo": (0.5, 0.0),
    "Zhaole Sun": (0.5, 1.0),
    "Zhengjie Shu": (0.5, 0.5),
    "Wanli Xing": (0.5, 1.0),
    "Yinqiang Zhang": (0.5, 0.1),
    "Yotsen Yan": (0.5, 0.15),
}
# User-supplied contact updates take precedence over the original collection.
EMAIL_OVERRIDES = {
    "Kun Song": ["kunsong112@gmail.com"],
    "Tengye Xu": ["xutengyehku@connect.hku.hk"],
    "Junxiao Lin": ["jxlin1@gmail.com"],
}
# User-supplied research updates take precedence over the original collection.
RESEARCH_OVERRIDES = {
    "Zhanteng Xie": "Navigation",
}
# Confirmed corrections take precedence over the original collection.
EXCLUDED_MEMBERS = {"Songyuan Su"}
MEMBER_OVERRIDES = {
    "Zhanteng Xie": {"year": 2025},
    "Zhaole Sun": {"alumni": False, "departure": ""},
    "Wentao Chen": {"alumni": False, "departure": ""},
    "Shijie Lin": {"role": "PostDoc", "year": 2026, "alumni": False, "departure": ""},
    "Wanli Xing": {"destination": "Sharpa"},
    "Chen Wang": {"destination": "AgiBot"},
    "Lei Yang": {"departure": "2023"},  # User-confirmed lab period: 2021-2023.
    # HKU postdoc: 2023.06-2024.11 (profile checked 2026-10-11).
    # https://cmee.nefu.edu.cn/info/1075/6397.htm
    "Jiaming Qi": {"departure": "November 2024"},
}
ROLE_LABELS = {
    "PostDoc": "Postdoc",
    "PhD": "PhD",
    "Master": "Master",
    "Visiting": "Visiting Student",
}
GROUPS = [
    ("PostDoc", "postdocs", "Postdocs", "Year indicates when the member joined the lab."),
    ("PhD", "phd", "PhD Students", "Year indicates when the student entered the program."),
    ("Master", "masters", "Master Students", "Year indicates when the student entered the program."),
    ("Visiting", "visitors", "Visiting Students", "Year indicates when the member joined the lab."),
]
ICONS = {
    "Homepage": '<path d="m3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9"/>',
    "Email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
    "Google Scholar": '<path d="m2 8 10-5 10 5-10 5zM6 10v6c4 3 8 3 12 0v-6M22 8v9"/>',
}


def normalize_name(value):
    if value in NAME_OVERRIDES:
        return NAME_OVERRIDES[value]
    # Family name first; preserve compound given names such as Ian Leong Ting.
    parts = re.split(r"[\s,，]+", value.strip())
    if len(parts) < 2 or not all(re.fullmatch(r"[A-Za-z'-]+", part) for part in parts):
        raise ValueError("Expected a full family-name-first name: " + value)
    return " ".join(part.title() for part in parts[1:] + parts[:1])


def normalize_homepage(value):
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    url = urlsplit(value)
    if (url.scheme not in {"https", "http"} or not url.hostname
            or "." not in url.hostname or re.search(r"\s", value)
            or url.username or url.password):
        raise ValueError("Invalid profile URL: " + value)
    return value


def normalize_departure(value):
    season = re.fullmatch(r"(\d{4})\s+(spring|summer|fall|winter|october)", value, re.I)
    if season:
        return season[2].title() + " " + season[1]
    month = re.fullmatch(r"(\d{4})[.-](\d{1,2})", value)
    if month and 1 <= int(month[2]) <= 12:
        return month_name[int(month[2])] + " " + month[1]
    if value == "2022-2025(post-doc)":
        return "2025"
    return value


def conflicting_dates(member):
    departure_year = re.search(r"\b(?:19|20)\d{2}\b", member["departure"])
    return bool(member["alumni"] and departure_year and int(departure_year[0]) < member["year"])


def validate_members(members):
    if not members:
        raise ValueError("The member collection is empty")
    names = [member["name"].casefold() for member in members]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate member names")
    for member in members:
        if member["role"] not in ROLE_LABELS:
            raise ValueError("Unknown member category: " + member["role"])
        if not isinstance(member["year"], int) or not 1900 <= member["year"] <= 2099:
            raise ValueError("Invalid joining year for " + member["name"])
        if not isinstance(member["alumni"], bool):
            raise ValueError("Invalid alumni status for " + member["name"])
        member["homepage"] = normalize_homepage(member["homepage"])
        photo_keys = ("source_photo", "photo", "portrait")
        # Alumni are rendered as text rows and may have no supplied photo.
        if not (member["alumni"] and all(member.get(key) is None for key in photo_keys)):
            for key in photo_keys:
                filename = member[key]
                if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
                    raise ValueError("Photo reference must be a filename: " + str(filename))
        if conflicting_dates(member):
            print("WARNING: Conflicting dates for " + member["name"] + ": joined "
                  + str(member["year"]) + ", left " + member["departure"]
                  + ". Website dates will be marked 'To be confirmed'.")


def read_members(workbook):
    """Read only source fields needed by the website, not submission metadata."""
    with ZipFile(workbook) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = [
                "".join(item.itertext())
                for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", NS)
            ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall("m:sheetData/m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                column = re.sub(r"\d", "", cell.get("r"))
                value_node = cell.find("m:v", NS)
                value = value_node.text if value_node is not None else ""
                if cell.get("t") == "s" and value:
                    value = strings[int(value)]
                elif cell.get("t") == "inlineStr":
                    value = "".join(cell.find("m:is", NS).itertext())
                values[column] = str(value or "").strip()
            if int(row.get("r")) > 1 and values.get("B"):
                values["row"] = int(row.get("r"))
                rows.append(values)

    members = []
    for row in rows:
        name = normalize_name(row["B"])
        if name in EXCLUDED_MEMBERS:
            continue
        role = row["D"]
        if role not in ROLE_LABELS:
            raise ValueError("Unknown member category: " + role)
        year_match = re.search(r"\b(?:19|20)\d{2}\b", row["C"])
        if not year_match:
            raise ValueError("Missing admission/joining year for " + name)
        source_photo = PHOTO_OVERRIDES.get(name, row["G"])
        if Path(source_photo).name != source_photo:
            raise ValueError("Photo reference must be a filename: " + source_photo)
        extension = Path(source_photo).suffix.lower()
        if extension in {".jpeg", ".jpg"}:
            extension = ".jpg"
        if extension not in {".jpg", ".png", ".webp"}:
            raise ValueError("Unsupported photo format: " + extension)
        stem = re.sub(r"[^A-Za-z0-9_-]", "_", name)
        homepage = normalize_homepage(row.get("I", ""))
        # The template has email icons. Do not turn other contact data into emails.
        emails = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", row.get("K", ""))
        emails = EMAIL_OVERRIDES.get(name, emails)
        if row.get("E") not in {"是", "否"}:
            raise ValueError("Unknown alumni status for " + name)
        departure = normalize_departure(row.get("F", ""))
        research = row.get("H", "")
        if research:
            research = RESEARCH_TEXT.get(research, research)
        research = RESEARCH_OVERRIDES.get(name, research)
        member = {
            "name": name,
            "role": role,
            "year": int(year_match.group()),
            "alumni": row["E"] == "是",
            "departure": departure,
            "research": research,
            "homepage": homepage,
            "emails": emails,
            "destination": DESTINATIONS.get(row.get("J", ""), row.get("J", "")),
            "source_photo": source_photo,
            "photo": stem + extension,
            "portrait": stem + ".webp",
            "row": row["row"],
        }
        member.update(MEMBER_OVERRIDES.get(name, {}))
        members.append(member)
    return members


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge_additions(members, additions):
    """Retain reviewed profiles that were supplied outside the collection form."""
    merged = {member["name"].casefold(): dict(member) for member in members}
    if len(merged) != len(members):
        raise ValueError("Duplicate member names")
    seen = set()
    for addition in additions:
        key = addition["name"].casefold()
        if key in seen:
            raise ValueError("Duplicate additional member: " + addition["name"])
        seen.add(key)
        merged[key] = {**merged.get(key, {}), **addition}
    return list(merged.values())


def prepare_photos(members, source_dir=None):
    """Preflight all photos, then copy imports without modifying raw files."""
    photo_members = [member for member in members if member["photo"]]
    photo_dir = source_dir or PHOTOS
    files = {path.name.casefold(): path for path in photo_dir.iterdir() if path.is_file()}
    local_files = {path.name.casefold(): path for path in PHOTOS.iterdir() if path.is_file()}
    planned = []
    target_names = [member["photo"].casefold() for member in photo_members]
    if len(target_names) != len(set(target_names)):
        raise ValueError("Duplicate normalized photo names")
    for member in photo_members:
        # Website-sourced profiles use saved local photos even during a raw import.
        source_files = local_files if member.get("source_url") else files
        source_parent = PHOTOS if member.get("source_url") else photo_dir
        if source_dir and member["name"] in PHOTO_OVERRIDES:
            source_parent = RAW
            source_files = {path.name.casefold(): path for path in RAW.iterdir() if path.is_file()}
        old = source_files.get(member["source_photo"].casefold())
        normalized = source_files.get(member["photo"].casefold())
        if old and normalized and old != normalized:
            raise ValueError("Both old and normalized photos exist for " + member["name"])
        source = old or normalized
        if source is None:
            raise FileNotFoundError(member["source_photo"])
        target = PHOTOS / member["photo"]
        if source.resolve().parent != source_parent.resolve() or target.resolve().parent != PHOTOS.resolve():
            raise ValueError("Photo path escaped the photo directory")
        with Image.open(source) as original:
            original.verify()
        planned.append((member, source, target, digest(source)))
    if len({source.resolve() for _, source, _, _ in planned}) != len(planned):
        raise ValueError("The same photo is assigned to multiple members")

    PHOTOS.mkdir(exist_ok=True)
    PORTRAITS.mkdir(exist_ok=True)
    manifest = []
    for member, source, target, before_hash in planned:
        if source != target and (not target.exists() or digest(target) != before_hash):
            shutil.copy2(source, target)
        if digest(target) != before_hash:
            raise ValueError("Original photo changed during copy: " + target.name)
        with Image.open(target) as original:
            upright = ImageOps.exif_transpose(original).convert("RGB")
            size = min(480, *upright.size)
            portrait = ImageOps.fit(
                upright, (size, size),
                method=Image.Resampling.LANCZOS,
                centering=CROP_CENTERS.get(member["name"], (0.5, 0.35)),
            )
            portrait.save(PORTRAITS / member["portrait"], "WEBP", quality=88, method=6)
        entry = {
            "name": member["name"],
            **({"source_url": member["source_url"], "photo_source_url": member["photo_source_url"]}
               if member.get("source_url") else
               {"source_file": "raw/" + PHOTO_OVERRIDES[member["name"]]}
               if member["name"] in PHOTO_OVERRIDES else {"source_cell": "G" + str(member["row"])}),
            "original_filename": member["source_photo"],
            "filename": member["photo"],
            "web_portrait": "portraits/" + member["portrait"],
            "sha256": before_hash,
        }
        manifest.append(entry)
    (PEOPLE / "photo-filenames.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def profile_link(url, label, name):
    return (
        '<a href="' + escape(url, quote=True) + '" aria-label="' + escape(name + " — " + label, quote=True)
        + '" title="' + label + '">'
        '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        + ICONS[label] + "</svg></a>"
    )


def person_card(member):
    name = escape(member["name"])
    links = []
    if member["homepage"]:
        label = "Google Scholar" if urlsplit(member["homepage"]).netloc == "scholar.google.com" else "Homepage"
        links.append(profile_link(member["homepage"], label, member["name"]))
    links.extend(profile_link("mailto:" + email, "Email", member["name"]) for email in member["emails"])
    research = escape(member["research"]) if member["research"] else '<span class="research-pending">To be added.</span>'
    links_html = '\n            <div class="person-links">' + "".join(links) + "</div>" if links else ""
    return (
        '          <article class="person" data-entry-year="' + str(member["year"]) + '">\n'
        '            <img src="people/portraits/' + member["portrait"] + '" alt="' + name
        + '" width="480" height="480" loading="lazy" decoding="async">\n'
        '            <h3 class="person-name">' + name + "</h3>\n"
        '            <p class="person-role">' + ROLE_LABELS[member["role"]] + " (" + str(member["year"]) + ")</p>\n"
        '            <p class="person-research"><span>Research:</span> ' + research + "</p>"
        + links_html + "\n          </article>"
    )


def render_members(members):
    sections = []
    for role, section_id, label, note in GROUPS:
        current = sorted(
            (member for member in members if member["role"] == role and not member["alumni"]),
            key=lambda member: (member["year"], member.get("row") or 0),
        )
        section = '    <section class="content-section" aria-labelledby="' + section_id + '-title">\n'
        section += '      <h2 id="' + section_id + '-title">' + label + "</h2>\n"
        if current:
            section += '      <p class="section-note">' + note + "</p>\n"
            section += '      <div class="people-grid">\n' + "\n".join(person_card(member) for member in current) + "\n      </div>\n"
        else:
            section += '      <p class="section-empty">Profiles will be added here.</p>\n'
        sections.append(section + "    </section>")

    alumni_section = (
        '    <section class="content-section" aria-labelledby="alumni-title">\n'
        '      <h2 id="alumni-title">Alumni</h2>\n'
        '      <p class="section-note">Dates indicate the period at the lab.</p>'
    )
    for role, _, label, _ in GROUPS:
        former = sorted(
            (member for member in members if member["role"] == role and member["alumni"]),
            key=lambda member: (member["year"], member.get("row") or 0),
        )
        if not former:
            continue
        alumni_section += (
            "\n      <h3>Former " + label + "</h3>\n"
            '      <table class="alumni people-alumni">\n'
            "        <thead><tr><th scope=\"col\">Name</th><th scope=\"col\">Role &amp; years</th>"
            "<th scope=\"col\">Current position</th><th scope=\"col\">Research</th></tr></thead>\n"
            "        <tbody>\n"
        )
        for member in former:
            name = escape(member["name"])
            if member["homepage"]:
                name = '<a href="' + escape(member["homepage"], quote=True) + '">' + name + "</a>"
            if member["emails"]:
                name += '<div class="person-links">' + "".join(
                    profile_link("mailto:" + email, "Email", member["name"])
                    for email in member["emails"]
                ) + "</div>"
            period = ("To be confirmed" if conflicting_dates(member) else
                      str(member["year"]) + "–" + (member["departure"] or "To be added"))
            fields = [
                ("Name", name),
                ("Role & years", ROLE_LABELS[role] + "<br>" + escape(period)),
                ("Current position", escape(member["destination"] or "To be added.")),
                ("Research", escape(member["research"] or "To be added.")),
            ]
            alumni_section += "          <tr>" + "".join(
                '<td data-label="' + escape(label, quote=True) + '">' + value + "</td>"
                for label, value in fields
            ) + "</tr>\n"
        alumni_section += "        </tbody>\n      </table>"
    sections.append(alumni_section + "\n    </section>")
    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-raw", action="store_true",
                        help="Import the workbook and images in people/raw (read-only)")
    args = parser.parse_args()
    workbook = None
    source_dir = None
    if args.import_raw:
        workbooks = [path for path in RAW.glob("*.xlsx") if not path.name.startswith("~$")]
        if len(workbooks) != 1:
            raise ValueError("Expected exactly one .xlsx collection in people/raw")
        workbook = workbooks[0]
        source_dir = RAW / "图片"
    elif not DATA.exists():
        # Backward compatibility with the first, smaller collection.
        workbook = PEOPLE / "data.xlsx"
    source_hash = digest(workbook) if workbook else None
    members = read_members(workbook) if workbook else json.loads(DATA.read_text(encoding="utf-8"))
    additions = json.loads(ADDITIONS.read_text(encoding="utf-8")) if ADDITIONS.exists() else []
    members = merge_additions(members, additions)
    members = [member for member in members if member["name"] not in EXCLUDED_MEMBERS]
    validate_members(members)
    if args.import_raw and DATA.exists():
        previous = json.loads(DATA.read_text(encoding="utf-8"))
        missing = ({member["name"] for member in previous} - EXCLUDED_MEMBERS
                   - {member["name"] for member in members})
        if missing:
            raise ValueError("Import would remove existing members: " + ", ".join(sorted(missing)))
    page_path = ROOT / "people.html"
    page = page_path.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError("Expected one pair of People data markers")
    content = render_members(members)
    prepare_photos(members, source_dir)
    if workbook and digest(workbook) != source_hash:
        raise ValueError("Source workbook changed")
    DATA.write_text(json.dumps(members, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before, rest = page.split(START, 1)
    _, after = rest.split(END, 1)
    page_path.write_text(before + START + "\n" + content + "\n" + END + after, encoding="utf-8")
    counts = Counter(("Alumni" if member["alumni"] else member["role"]) for member in members)
    print("Updated People:", dict(counts))
    print("Original photos:", sum(bool(member["photo"]) for member in members), "(content hashes verified)")
    print("Normalized data:", DATA.relative_to(ROOT))
    if workbook:
        print("Source workbook unchanged:", workbook.relative_to(ROOT))


if __name__ == "__main__":
    main()
