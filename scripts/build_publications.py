"""Build a static publication list from Scholar and verified additions.

python scripts/build_publications.py             # render the saved data
python scripts/build_publications.py --refresh   # fetch Scholar, then render

Requires beautifulsoup4 for parsing Scholar pages. Browsing the website itself
does not require Python or access to Google Scholar.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "publications" / "scholar.json"
ADDITIONS = ROOT / "publications" / "additions.json"
PAGE = ROOT / "publications.html"
USER_ID = "YYT8-7kAAAAJ"
PROFILE_URL = "https://scholar.google.com/citations?" + urlencode({
    "hl": "zh-CN", "user": USER_ID, "view_op": "list_works", "sortby": "pubdate",
})
FIRST_YEAR = 2020
START = "    <!-- PUBLICATIONS DATA START -->"
END = "    <!-- PUBLICATIONS DATA END -->"


def fetch(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=25) as response:
        return BeautifulSoup(response.read(), "html.parser")


def read_profile():
    """Follow normal profile pagination, rejecting incomplete/error responses."""
    records = []
    seen = set()
    for offset in range(0, 5000, 100):
        url = PROFILE_URL + "&pagesize=100&cstart=" + str(offset)
        soup = fetch(url)
        author = soup.select_one("#gsc_prf_in")
        if not author or author.get_text(" ", strip=True) != "Jia Pan":
            raise ValueError("Scholar did not return the expected Jia Pan profile.")
        rows = soup.select("tr.gsc_a_tr")
        if not rows:
            raise ValueError("Scholar returned an empty or blocked page; the saved data is retained.")
        for row in rows:
            title = row.select_one(".gsc_a_at")
            if not title:
                continue
            detail_url = urljoin(url, title["href"])
            key = parse_qs(urlsplit(detail_url).query).get("citation_for_view", [""])[0]
            if not key or key in seen:
                raise ValueError("Missing or repeated Scholar record ID while paging.")
            seen.add(key)
            secondary = row.select(".gsc_a_t .gs_gray")
            year = row.select_one(".gsc_a_y")
            records.append({
                "title": title.get_text(" ", strip=True),
                "authors": secondary[0].get_text(" ", strip=True) if secondary else "",
                "venue": secondary[1].get_text(" ", strip=True) if len(secondary) > 1 else "",
                "year": year.get_text(" ", strip=True) if year else "",
                "scholar_url": detail_url,
            })
        print("Read Scholar records:", len(records), flush=True)
        more = soup.select_one("#gsc_bpf_more")
        if more is None:
            raise ValueError("Cannot verify the end of the Scholar list.")
        if more.has_attr("disabled"):
            return records
        time.sleep(1)
    raise ValueError("Unexpectedly large profile; the saved data is retained.")


def normalize_records(raw):
    current_year = datetime.now().year
    selected = []
    for row in raw:
        year_text = str(row.get("year", "")).strip()
        if not year_text.isdigit() or not FIRST_YEAR <= int(year_text) <= current_year:
            continue
        query = parse_qs(urlsplit(row["scholar_url"]).query)
        key = query.get("citation_for_view", [""])[0]
        if not key.startswith(USER_ID + ":"):
            raise ValueError("Record belongs to another Scholar profile.")
        selected.append({
            "id": key,
            "title": row["title"].strip(),
            "authors": row["authors"].strip(),
            "authors_truncated": bool(re.search(r"\.{3}|…", row["authors"])),
            "venue": re.sub(r"\s+,", ",", row["venue"]).strip(),
            "year": int(year_text),
            "scholar_url": "https://scholar.google.com/citations?" + urlencode({
                "view_op": "view_citation", "hl": "zh-CN",
                "user": USER_ID, "citation_for_view": key,
            }),
        })
    selected.sort(key=lambda record: record["year"], reverse=True)
    if not selected or len({record["id"] for record in selected}) != len(selected):
        raise ValueError("The selected records are empty or contain duplicate IDs.")
    return selected


def expand_authors(records):
    """Expand only lists visibly truncated by Scholar; preserve all other text."""
    pending = [record for record in records if record["authors_truncated"]]
    for index, record in enumerate(pending, 1):
        try:
            soup = fetch(record["scholar_url"])
            fields = {}
            for row in soup.select(".gs_scl"):
                label = row.select_one(".gsc_oci_field")
                value = row.select_one(".gsc_oci_value")
                if label is not None and value is not None:
                    fields[label.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
            full = fields.get("Authors") or fields.get("作者")
            if not full:
                raise ValueError("No author field returned by Scholar.")
            record["authors_full"] = full
            title_link = soup.select_one("#gsc_oci_title a[href]")
            if title_link:
                target = title_link["href"]
                if urlsplit(target).scheme in {"https", "http"}:
                    record["paper_url"] = target
            print("Expanded author lists:", str(index) + "/" + str(len(pending)), flush=True)
        except Exception as error:
            # A blocked detail endpoint must not trigger retries or lose the list.
            print("Detail lookup stopped:", type(error).__name__, str(error), flush=True)
            break
        time.sleep(0.5)


def save_snapshot(raw, records):
    snapshot = {
        "source_url": PROFILE_URL,
        "profile_name": "Jia Pan",
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "first_year": FIRST_YEAR,
        "through_year": datetime.now().year,
        "profile_record_count": len(raw),
        "undated_records_excluded": sum(not str(row.get("year", "")).strip() for row in raw),
        "publication_count": len(records),
        "publications": records,
    }
    SNAPSHOT.parent.mkdir(exist_ok=True)
    temporary = SNAPSHOT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(SNAPSHOT)
    return snapshot


def author_html(record):
    authors = record.get("authors_full") or record["authors"]
    # Emphasize only an exact Jia Pan token, without guessing other identities.
    return ", ".join(
        "<strong>" + escape(name.strip()) + "</strong>"
        if name.strip() in {"J Pan", "Jia Pan"} else escape(name.strip())
        for name in authors.split(",")
    )


def merge_additions(snapshot, additions):
    """Keep publisher-sourced additions across Scholar refreshes, without duplicates."""
    records = [dict(record) for record in snapshot["publications"]]
    seen = set()
    for addition in additions:
        for key in ("id", "title", "authors", "venue", "paper_url"):
            if not isinstance(addition.get(key), str) or not addition[key].strip():
                raise ValueError("Publication addition is missing " + key)
        if addition["id"] in seen:
            raise ValueError("Duplicate publication addition ID: " + addition["id"])
        seen.add(addition["id"])
        if not isinstance(addition.get("year"), int) or addition["year"] < FIRST_YEAR:
            raise ValueError("Invalid publication year: " + addition["id"])
        url = urlsplit(addition["paper_url"])
        if url.scheme not in {"http", "https"} or not url.netloc:
            raise ValueError("Invalid paper URL: " + addition["id"])
        title_key = re.sub(r"\W+", "", addition["title"]).casefold()
        doi = addition.get("doi", "").casefold()
        matches = [index for index, record in enumerate(records) if (
            record["id"] == addition["id"]
            or (doi and record.get("doi", "").casefold() == doi)
            or re.sub(r"\W+", "", record["title"]).casefold() == title_key
        )]
        if len(matches) > 1:
            raise ValueError("Ambiguous publication match: " + addition["title"])
        if matches:
            index = matches[0]
            original = records[index]
            merged = {**original, **addition, "id": original["id"]}
            if "authors_full" not in addition:
                merged.pop("authors_full", None)
            records[index] = merged
        else:
            records.insert(0, dict(addition))
    records.sort(key=lambda record: record["year"], reverse=True)
    return {**snapshot, "publications": records, "publication_count": len(records)}


def publication_html(record):
    title = escape(record["title"])
    scholar_url = record.get("scholar_url")
    title_url = escape(scholar_url or record["paper_url"], quote=True)
    links = []
    paper_url = record.get("paper_url")
    if paper_url:
        links.append('<a href="' + escape(paper_url, quote=True) + '">Paper</a>')
    if scholar_url:
        links.append('<a href="' + escape(scholar_url, quote=True) + '">Google Scholar</a>')
    if record.get("doi"):
        links.append('<a href="https://doi.org/' + escape(record["doi"], quote=True) + '">DOI</a>')
    id_attribute = "data-scholar-id" if scholar_url else "data-publication-id"
    return (
        '        <article class="pub pub-text-only" ' + id_attribute + '="' + escape(record["id"], quote=True) + '">\n'
        "          <div>\n"
        '            <h3 class="pub-title"><a href="' + title_url + '">' + title + "</a></h3>\n"
        '            <p class="pub-authors">' + author_html(record) + "</p>\n"
        '            <p class="pub-venue">' + escape(record["venue"]) + "</p>\n"
        '            <div class="pub-links">' + "".join(links) + "</div>\n"
        "          </div>\n"
        "        </article>"
    )


def render(snapshot):
    records = snapshot["publications"]
    counts = Counter(record["year"] for record in records)
    years = sorted(counts, reverse=True)
    navigation = '    <nav class="publication-years" aria-label="Publication years">\n'
    navigation += "\n".join(
        '      <a href="#year-' + str(year) + '">' + str(year) + "</a>" for year in years
    )
    navigation += "\n    </nav>"
    sections = [navigation]
    for year in years:
        section = (
            '    <section class="content-section publication-section" aria-labelledby="year-' + str(year) + '">\n'
            '      <h2 id="year-' + str(year) + '">' + str(year)
            + ' <span class="publication-count">' + str(counts[year]) + " publications</span></h2>\n"
        )
        section += "\n".join(publication_html(record) for record in records if record["year"] == year)
        sections.append(section + "\n    </section>")
    sections.append('    <p class="publications-back"><a href="#main-content">Back to top ↑</a></p>')
    return "\n\n".join(sections)


def write_page(snapshot):
    page = PAGE.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError("Expected one pair of publication data markers.")
    before, remainder = page.split(START, 1)
    _, after = remainder.split(END, 1)
    PAGE.write_text(before + START + "\n" + render(snapshot) + "\n" + END + after, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch a new Scholar snapshot before rendering.")
    args = parser.parse_args()
    if args.refresh:
        raw = read_profile()
        records = normalize_records(raw)
        expand_authors(records)
        snapshot = save_snapshot(raw, records)
    else:
        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    additions = json.loads(ADDITIONS.read_text(encoding="utf-8")) if ADDITIONS.exists() else []
    snapshot = merge_additions(snapshot, additions)
    write_page(snapshot)
    print("Rendered", snapshot["publication_count"], "publications from", snapshot["first_year"], "onwards.")


if __name__ == "__main__":
    main()
