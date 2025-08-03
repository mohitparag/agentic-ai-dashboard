import streamlit as st
from serpapi import GoogleSearch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import time

# ✅ SerpAPI Key
SERPAPI_KEY = "b95ec969209ac2c30002fb22109ed911ca37e5d41b98e32bee85c7abd4827063"
styles = getSampleStyleSheet()

# --------------------- AGENTS ---------------------
def search_agent(company_name):
    params = {"engine": "google", "q": f"{company_name} company profile details", "api_key": SERPAPI_KEY}
    results = GoogleSearch(params).get_dict()
    if "organic_results" in results:
        r = results["organic_results"][0]
        return {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
    return {"error": "No company details found"}

def hiring_agent(company_name):
    params = {"engine": "google_jobs", "q": f"{company_name} jobs", "api_key": SERPAPI_KEY}
    results = GoogleSearch(params).get_dict()
    jobs = []
    for j in results.get("jobs_results", []):
        jobs.append([
            j.get("title", "N/A"),
            j.get("location", "N/A"),
            j.get("detected_extensions", {}).get("posted_at", "N/A"),
            j.get("apply_options", [{}])[0].get("link", "#")
        ])
    return jobs

def decision_maker_agent_free(company_name, max_leads=10):
    contacts, seen_links = [], set()
    per_page = 10
    for page in range((max_leads // per_page) + 1):
        params = {"engine": "google", "q": f'"HR Head" OR "Talent Acquisition" site:linkedin.com/in "{company_name}"',
                  "api_key": SERPAPI_KEY, "start": page * per_page}
        results = GoogleSearch(params).get_dict()
        for r in results.get("organic_results", []):
            link = r.get("link", "#")
            if link not in seen_links:
                contacts.append([r.get("title", "N/A"), "LinkedIn Profile", link])
                seen_links.add(link)
        if len(contacts) >= max_leads: break
        time.sleep(1)
    return contacts[:max_leads]

# --------------------- PDF GENERATOR (With Blue Underlined Links) ---------------------
def generate_styled_pdf(company_info, hiring_info, decision_makers, filename="Company_Report_Final.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    # Title
    elements.append(Paragraph("<para align='center'><b><font size=16>Company Report</font></b></para>", styles['Title']))
    elements.append(Spacer(1, 20))

    # Company Info
    elements.append(Paragraph(f"<b>🏢 {company_info['title']}</b>", styles['Heading2']))
    elements.append(Paragraph(company_info['snippet'], styles['BodyText']))
    elements.append(Paragraph(f'<font color="blue"><u><a href="{company_info["link"]}">🌐 Visit Company Website</a></u></font>', styles['BodyText']))
    elements.append(Spacer(1, 20))

    # Hiring Info Table
    elements.append(Paragraph("<b>💼 Current Hiring Positions</b>", styles['Heading2']))
    hiring_table_data = [[Paragraph("<b>Position</b>", styles['BodyText']),
                          Paragraph("<b>Location</b>", styles['BodyText']),
                          Paragraph("<b>Posted</b>", styles['BodyText'])]]

    for job in hiring_info:
        job_title = Paragraph(f'<font color="blue"><u><a href="{job[3]}">{job[0]}</a></u></font>', styles['BodyText'])
        hiring_table_data.append([job_title, job[1], job[2]])

    hiring_table = Table(hiring_table_data, colWidths=[200, 120, 80])
    hiring_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "TOP")
    ]))
    elements.append(hiring_table)
    elements.append(Spacer(1, 20))

    # Decision Makers Table
    elements.append(Paragraph("<b>👥 Decision Makers</b>", styles['Heading2']))
    dm_table_data = [[Paragraph("<b>Name</b>", styles['BodyText']),
                      Paragraph("<b>LinkedIn</b>", styles['BodyText'])]]

    for dm in decision_makers:
        linkedin_link = Paragraph(f'<font color="blue"><u><a href="{dm[2]}">LinkedIn Profile</a></u></font>', styles['BodyText'])
        dm_table_data.append([Paragraph(dm[0], styles['BodyText']), linkedin_link])

    dm_table = Table(dm_table_data, colWidths=[230, 150])
    dm_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "TOP")
    ]))
    elements.append(dm_table)

    doc.build(elements)
    return filename

# --------------------- STREAMLIT UI ---------------------
st.set_page_config(page_title="Agentic AI – Company Research", layout="wide")
st.title("🤖 Agentic AI – Company Research Dashboard (Final)")

st.markdown("""
### ✅ Features:
- 📌 Live company & HR data from web
- 📌 Clickable blue underlined job & LinkedIn links
- 📌 Professionally formatted PDF (with hyperlinks)
""")

company_name = st.text_input("🔍 Enter Company Name:")

if st.button("🚀 Run Analysis") and company_name:
    st.info("⏳ Fetching data, please wait...")

    company_info = search_agent(company_name)
    hiring_info = hiring_agent(company_name)
    decision_makers = decision_maker_agent_free(company_name, max_leads=10)

    # Display Company Info
    st.subheader("🏢 Company Overview")
    if "error" in company_info:
        st.error("No company details found.")
    else:
        st.success(company_info['title'])
        st.write(company_info['snippet'])
        st.markdown(f"🌐 [Visit Website]({company_info['link']})")

    # Hiring Info
    st.subheader("💼 Current Hiring Positions")
    if hiring_info:
        for job in hiring_info:
            st.markdown(f"- [{job[0]}]({job[3]}) – {job[1]} – Posted: {job[2]}")
    else:
        st.warning("No active job postings found.")

    # Decision Makers
    st.subheader("👥 Decision Makers")
    if decision_makers:
        for dm in decision_makers:
            st.markdown(f"- {dm[0]} → [LinkedIn Profile]({dm[2]})")
    else:
        st.warning("No HR contacts found.")

    # Generate Styled PDF
    pdf_filename = generate_styled_pdf(company_info, hiring_info, decision_makers)
    with open(pdf_filename, "rb") as f:
        st.download_button("📄 Download Professional PDF Report", data=f, file_name=pdf_filename, mime="application/pdf")
