"""
Build site/public/research.html from docs/DATA-METHODS.md, with a downloads list on top.
Usage: python pipeline/build_research_page.py
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import pathlib
import markdown

DOWNLOADS = [
    ("/data/river_stats.json", "River statistics", "Every 500 m of the flood path and four control rivers, for all eight 12-day periods: mean change and share of pixels changed by more than 3 dB."),
    ("/data/flowpath.geojson", "River paths", "The traced flood path, the control rivers and the kilometre marks."),
    ("/data/series/series.json", "Radar series, description", "Grid, dates and how to turn pixel values into decibels for the ten images hh-YYYYMMDD.png in the same folder (for example /data/series/hh-20260819.png)."),
    ("/data/glacier/glacier_season.json", "Glacier table", "Median echo per height band and date, and the share of ice more than 3 dB below its 20 June value."),
    ("/data/glacial_lakes.geojson", "Glacial lakes", "The 12 lakes of NASA's HMA_GLI inventory (2015 to 2018) inside the study box."),
    ("/data/terrain.json", "Terrain layers, description", "How flowdir.png (flow directions) and lowground.png (low ground) are laid out."),
    ("/data/layers.json", "Map layers", "Every change and radar tile layer with its source files and colour scale."),
]

md = pathlib.Path("docs/DATA-METHODS.md").read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables", "fenced_code"])
body = body.replace("<h1>", '<p><a href="/">Back to the map</a></p>\n<h1>', 1)
rows = "\n".join(f'<tr><td><a href="{u}" download>{t}</a></td><td>{d}</td></tr>' for u, t, d in DOWNLOADS)
downloads = f'<h2 id="downloads">Downloads</h2>\n<p>Click a spot on the map and press “Download CSV” for one place. For everything else:</p>\n<table><thead><tr><th>File</th><th>What is in it</th></tr></thead><tbody>\n{rows}\n</tbody></table>\n'
cut = body.index("<h2>The short version")
body = body[:cut] + downloads + body[cut:]
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data and methods: Rasuwa flood traced with NISAR</title>
<!-- SI disclosure: this page and the scripts it describes were written with SI assistance (Claude, Anthropic). -->
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="/page.css">
</head>
<body class="page">
{body}
</body>
</html>
"""
pathlib.Path("site/public/research.html").write_text(html, encoding="utf-8")
print("research.html", len(html))
