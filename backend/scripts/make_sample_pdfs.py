"""Generate small English test PDFs into ../sample_docs."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).resolve().parents[2] / "sample_docs"

DOCS = {
    "solar_energy.pdf": [
        ("Solar Energy Basics", [
            "Solar panels convert sunlight into electricity using photovoltaic cells made mostly of silicon.",
            "A typical residential solar panel has an efficiency between 15 and 22 percent.",
            "Most manufacturers guarantee that panels will still produce at least 80 percent of their rated power after 25 years.",
        ]),
        ("Costs and Maintenance", [
            "In 2023 the average installed cost of a home solar system was about 2.8 dollars per watt.",
            "Panels need very little maintenance; cleaning them twice a year is usually enough.",
            "Inverters typically need to be replaced after 10 to 15 years.",
        ]),
    ],
    "company_handbook.pdf": [
        ("Employee Handbook - Leave Policy", [
            "Full-time employees receive 21 days of paid annual leave per year.",
            "Unused annual leave can be carried over to the next year, up to a maximum of 5 days.",
            "Sick leave is 10 days per year and requires a medical certificate after 3 consecutive days.",
        ]),
        ("Remote Work", [
            "Employees may work remotely up to 2 days per week with manager approval.",
            "The company provides a one-time home-office allowance of 500 dollars.",
        ]),
    ],
}


def main():
    OUT.mkdir(exist_ok=True)
    styles = getSampleStyleSheet()
    for name, pages in DOCS.items():
        story = []
        for n, (title, paras) in enumerate(pages):
            if n:
                story.append(PageBreak())
            story.append(Paragraph(title, styles["Heading1"]))
            for p in paras:
                story += [Paragraph(p, styles["BodyText"]), Spacer(1, 10)]
        SimpleDocTemplate(str(OUT / name), pagesize=A4).build(story)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
