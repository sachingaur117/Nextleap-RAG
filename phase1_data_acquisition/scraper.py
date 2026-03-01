import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os

async def scrape_course(page, url):
    print(f"Scraping {url}...")
    await page.goto(url)
    
    # Wait for the main content to load
    try:
        await page.wait_for_selector('h1', timeout=10000)
    except Exception as e:
        print(f"Timeout waiting for h1 on {url}")

    # Scroll down to ensure all lazy loaded content appears
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight/5)")
        await asyncio.sleep(1)

    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'lxml')

    data = {
        "url": url,
        "title": "",
        "hero_details": [],
        "cost_info": {},
        "schedule": [],
        "instructors": [],
        "placement_support": [],
        "syllabus": []
    }

    # Title
    h1 = soup.find('h1')
    if h1:
        data["title"] = h1.get_text(strip=True)

    # 1. Hero details (Hours, duration, etc.)
    for div in soup.find_all('div'):
        text = div.get_text(separator=' ', strip=True)
        if "100+ Hours" in text and "Live Classes" in text and len(text) < 100:
            data["hero_details"].append("100+ Hours Live Classes")
        if "months" in text and len(text) < 50 and any(char.isdigit() for char in text):
            data["hero_details"].append(text)

    # De-duplicate hero details
    data["hero_details"] = list(set(data["hero_details"]))

    # 2. Cost and Cohort
    for p in soup.find_all(['p', 'div', 'span']):
        text = p.get_text(separator=' ', strip=True)
        if "Cohort" in text and "starts on" in text and len(text) < 60:
            data["cost_info"]["cohort_start"] = text
        if "₹" in text and "Cost" not in text and len(text) < 40:
            if "pricing" not in data["cost_info"]:
                data["cost_info"]["pricing"] = []
            if text not in data["cost_info"]["pricing"]:
                data["cost_info"]["pricing"].append(text)
        if "EMI from" in text and len(text) < 80:
            data["cost_info"]["emi"] = text
        if "Price increase" in text and len(text) < 80:
            data["cost_info"]["price_increase"] = text

    # 3. Placement Support
    for el in soup.find_all(['h2', 'h3', 'p', 'div']):
         text = el.get_text(separator=' ', strip=True)
         if "1 Year Placement Support" in text and len(text) < 100:
              data["placement_support"].append("1 Year Placement Support")
         if "Clear the cut-off marks" in text and len(text) < 200:
              data["placement_support"].append(text)
         if "Average" in text and "Salary" in text and "Lakhs" in text and len(text) < 60:
              data["placement_support"].append(text)
         if "Highest Salary" in text and "Lakhs" in text and len(text) < 60:
              data["placement_support"].append(text)
    
    data["placement_support"] = list(set(data["placement_support"]))

    # 4. Schedule
    schedule_heading = soup.find(string=lambda t: t and "Live Class Schedule" in t)
    if schedule_heading:
        parent_section = schedule_heading.find_parent('div', class_=lambda c: c and ('grid' in c or 'flex' in c))
        if parent_section:
             schedule_texts = parent_section.get_text(separator='\n', strip=True).split('\n')
             data["schedule"] = [s.strip() for s in schedule_texts if s.strip() and "Schedule" not in s]

    # 5. Instructors - Strategy 1 (From the detailed text block usually following an H3 "Learn from Instructors...")
    detailed_instructor_heading = soup.find(lambda tag: tag.name in ["h2", "h3"] and "Learn from Instructors" in tag.get_text())
    if detailed_instructor_heading:
        # The list usually follows immediately or soon after
        ul_element = detailed_instructor_heading.find_next_sibling("ul")
        if ul_element:
            for li in ul_element.find_all("li"):
                data["instructors"].append(li.get_text(strip=True))
                
    # 5. Instructors - Strategy 2 (Fallback to the "Learn Concepts From Our Instructors" grid section)
    if not data["instructors"]:
        instructor_heading = soup.find(string=lambda t: t and "Learn Concepts From Our Instructors" in t)
        if instructor_heading:
            parent_container = instructor_heading.find_parent('div')
            if parent_container:
                text_blobs = parent_container.get_text(separator='|', strip=True).split('|')
                current_instructor = []
                for item in text_blobs:
                     if item == "Learn Concepts From Our Instructors": continue
                     current_instructor.append(item)
                     if len(current_instructor) >= 3 or ("@" in item) or ("Founder" in item):
                         data["instructors"].append(" | ".join(current_instructor))
                         current_instructor = []

    return data

async def main():
    # Adding generative ai directly to check if it resolves (we found a valid pattern)
    urls = [
         "https://nextleap.app/course/product-management-course",
         "https://nextleap.app/course/ui-ux-design-course", 
         "https://nextleap.app/course/data-analyst-course",
         "https://nextleap.app/course/business-analyst-course",
         "https://nextleap.app/course/generative-ai-course"
    ]
    
    os.makedirs("data", exist_ok=True)
    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        for url in urls:
            try:
                course_data = await scrape_course(page, url)
                all_data.append(course_data)
                
                course_slug = url.split("/")[-1]
                with open(f"data/{course_slug}.json", "w", encoding="utf-8") as f:
                    json.dump(course_data, f, indent=4, ensure_ascii=False)
                    
                print(f"Saved data for {course_slug}")
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
