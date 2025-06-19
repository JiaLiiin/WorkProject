from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Import TimeoutException
import time
import json
import csv
from urllib.parse import urljoin

# --- Configuration ---
# IMPORTANT: Replace with the actual base URL of the website!
# Example: If the site is "https://example.com/members", use "https://example.com/"
BASE_URL = 'https://btbvn.vn' # <--- **UPDATE THIS URL**
# The URL of the page containing the dropdowns and member listings
MAIN_PAGE_URL = BASE_URL + '/' # <--- **UPDATE THIS URL**

# Output file names
OUTPUT_JSON_FILE = 'scraped_members_data_categorized.json'
OUTPUT_CSV_FILE = 'scraped_members_data_categorized.csv'

def setup_driver():
    """Sets up and returns a Safari WebDriver instance."""
    try:
        driver = webdriver.Safari()
        return driver
    except Exception as e:
        print(f"Error setting up Safari WebDriver: {e}")
        print("Please ensure 'Allow Remote Automation' is enabled in Safari's Develop menu.")
        return None

def extract_dropdown_options(soup, select_id):
    """Extracts options (text and value) from a select dropdown."""
    options_list = []
    select_element = soup.find('select', id=select_id)
    if select_element:
        for option in select_element.find_all('option'):
            text = option.get_text(strip=True)
            value = option.get('value', '').strip()
            # Exclude the default "選擇區域" or "行業分類" option if its value is empty
            if value:
                options_list.append({'text': text, 'value': value})
    return options_list

def extract_member_info_from_current_view(soup, current_region_text, current_industry_text):
    """
    Extracts member information from the currently displayed content on the page.
    """
    members_on_page = []
    # The container for member items is assumed to be `div#show_padding`
    show_padding_div = soup.find('div', id='show_padding')

    if show_padding_div:
        member_items = show_padding_div.find_all('div', class_='member-item')
        for item in member_items:
            member_id_p = item.find('p', class_='maso-info')
            member_name_h3 = item.find('h3', class_='member-info')
            member_name_a = member_name_h3.find('a') if member_name_h3 else None

            member_id = member_id_p.get_text(strip=True) if member_id_p else 'N/A'
            company_name_chinese = member_name_a.get_text(strip=True) if member_name_a else 'N/A'
            
            # Construct the full URL if href is relative
            relative_url = member_name_a['href'].strip() if member_name_a and member_name_a.get('href') else ''
            full_member_url = urljoin(MAIN_PAGE_URL, relative_url) if relative_url else 'N/A'

            member_data = {
                '會員編號': member_id,
                '公司名稱(中)': company_name_chinese,
                '詳細頁面網址': full_member_url,
                '所在區域': current_region_text,
                '所屬行業': current_industry_text
            }

            # Extract additional fields dynamically from the modal HTML structure if present
            # Look for div.row.m5.thongtinthanhvien-popup within the current item's modal if it exists in the page source
            # Note: This part assumes the modal HTML is directly accessible in the main page source,
            # which is typical if it's hidden by CSS/JS and not loaded dynamically after click.
            # If the modal content truly loads ONLY after clicking the link, a separate browse step would be needed.

            # Identify the modal ID from the member link's href if it's "NIA01476" style which maps to #exampleModal126
            # This is a bit of a guess based on the provided HTML fragment where modal ID seems to correlate with member ID.
            modal_id_from_href = relative_url.replace('.html', '') # Remove .html if present
            # Example: from "NIA01476" to "exampleModal126" requires a mapping or pattern.
            # Based on the provided HTML, it seems the modal IDs are 'exampleModal' + some number.
            # Let's assume there's a way to find the relevant modal for the current member item.
            # Given the previous context, modal ID might be dynamic or based on the data.
            # For robustness, we will try to find a modal that contains the member_id directly within its content.

            # Iterate through all modal-body divs to find the one related to the current member
            modal_body_elements = soup.find_all('div', class_='modal-body')
            for modal_body in modal_body_elements:
                modal_member_id_p = modal_body.find('label', string='會員編號:').find_next_sibling('div', class_='content-element-member').find('p') if modal_body.find('label', string='會員編號:') else None
                modal_member_id = modal_member_id_p.get_text(strip=True) if modal_member_id_p else None

                if modal_member_id == member_id:
                    # Found the correct modal body for this member, extract all key-value pairs
                    modal_label_elements = modal_body.find_all('label', class_='title-element-member')
                    for m_label in modal_label_elements:
                        m_label_text = m_label.get_text(strip=True).replace(':', '').strip()
                        m_content_div = m_label.find_next_sibling('div', class_='content-element-member')
                        if m_content_div:
                            m_content_text = m_content_div.find('p').get_text(strip=True) if m_content_div.find('p') else m_content_div.get_text(strip=True)
                            
                            # Handle special cases for social media/web links from image labels
                            if m_label.find('img', src='assets/images/web.png'):
                                link_tag = m_content_div.find('a', class_='hover-red')
                                member_data['網址'] = link_tag['href'].strip() if link_tag and link_tag.get('href') else ''
                            elif m_label.find('img', src='assets/images/facebook.png'):
                                link_tag = m_content_div.find('a', class_='hover-red')
                                member_data['Facebook'] = link_tag['href'].strip() if link_tag and link_tag.get('href') else ''
                            elif m_label.find('img', src='assets/images/line.png'):
                                link_tag = m_content_div.find('a', class_='hover-red')
                                member_data['Line'] = link_tag['href'].strip() if link_tag and link_tag.get('href') else ''
                            elif m_label.find('img', src='assets/images/wechat.png'):
                                link_tag = m_content_div.find('a', class_='hover-red')
                                member_data['WeChat'] = link_tag['href'].strip() if link_tag and link_tag.get('href') else ''
                            elif m_label_text: # General case for other text labels
                                member_data[m_label_text] = m_content_text
                    break # Found and processed the modal for this member, break from modal loop

            members_on_page.append(member_data)
    return members_on_page

def scrape_categorized_members():
    driver = setup_driver()
    if not driver:
        return

    all_scraped_members_data = []
    unique_member_keys = set() # To store (member_id, company_name_chinese) tuples to avoid duplicates

    try:
        print(f"Navigating to main page: {MAIN_PAGE_URL}...")
        driver.get(MAIN_PAGE_URL)

        # Give the page some time to load initial content and dropdowns
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "select-brand-list"))
        )
        print("Page loaded. Extracting dropdown options...")

        # Get initial page source to extract all options
        initial_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract all region options
        region_options = extract_dropdown_options(initial_soup, 'select-brand-list')
        if not region_options:
            print("No region options found. Exiting.")
            return []

        # Extract all industry options
        industry_options = extract_dropdown_options(initial_soup, 'select-nghe-list')
        if not industry_options:
            print("No industry options found. Exiting.")
            return []

        print(f"Found {len(region_options)} regions and {len(industry_options)} industries.")

        # Loop through each region
        for region_option in region_options:
            region_value = region_option['value']
            region_text = region_option['text']
            
            # Select the region in the live browser
            region_dropdown = Select(driver.find_element(By.ID, "select-brand-list"))
            region_dropdown.select_by_value(region_value)
            
            # Allow time for the page/AJAX to update after region selection
            time.sleep(2) # Adjust based on website responsiveness

            # Loop through each industry
            for industry_option in industry_options:
                industry_value = industry_option['value']
                industry_text = industry_option['text']

                # Select the industry in the live browser
                industry_dropdown = Select(driver.find_element(By.ID, "select-nghe-list"))
                industry_dropdown.select_by_value(industry_value)
                
                # Allow time for the page/AJAX to update after industry selection
                try:
                    # Wait for at least one member item to be present to indicate content loaded
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "member-item"))
                    )
                    print(f"  Scraping: 區域='{region_text}', 行業分類='{industry_text}'")
                except TimeoutException:
                    print(f"  No member items found for 區域='{region_text}', 行業分類='{industry_text}' after waiting. Skipping.")
                    continue # Skip to the next combination if no content loads

                # Get the page source after selecting both filters
                current_page_source = driver.page_source
                current_soup = BeautifulSoup(current_page_source, 'html.parser')

                # Extract data from the current view. Pass the full soup for modal lookup.
                members_on_view = extract_member_info_from_current_view(current_soup, region_text, industry_text)
                
                for member_data in members_on_view:
                    # Create a unique key for the member based on ID and Chinese name
                    member_id = member_data.get('會員編號')
                    company_name = member_data.get('公司名稱(中)')
                    unique_key = (member_id, company_name)
                    
                    if unique_key and unique_key not in unique_member_keys:
                        all_scraped_members_data.append(member_data)
                        unique_member_keys.add(unique_key)
                    # If unique_key is None (e.g., if member_id is 'N/A'), still add if not duplicate
                    elif not unique_key and member_data not in all_scraped_members_data:
                        all_scraped_members_data.append(member_data)
                
                # Add a small delay between each industry selection
                time.sleep(1)

            # Add a small delay after each region selection
            time.sleep(2)

    except Exception as e:
        print(f"An unexpected error occurred during the scraping process: {e}")
    finally:
        if driver:
            print("\nClosing Safari browser...")
            driver.quit()

    # --- Save the collected data ---
    if all_scraped_members_data:
        print(f"\n--- Saving Collected Data ({len(all_scraped_members_data)} unique member entries) ---")
        save_data_to_json(all_scraped_members_data, OUTPUT_JSON_FILE)
        save_data_to_csv(all_scraped_members_data, OUTPUT_CSV_FILE)
    else:
        print("\nNo member data was collected.")
    
    return all_scraped_members_data

def save_data_to_json(data, filename):
    """Saves a list of dictionaries to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def save_data_to_csv(data, filename):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        print("No data to save to CSV.")
        return

    all_keys = set()
    for item in data:
        all_keys.update(item.keys())
    fieldnames = sorted(list(all_keys))

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    print("Starting Selenium + BeautifulSoup extraction example for categorized members...")
    print("---------------------------------------")
    print("**IMPORTANT: Make sure to update 'BASE_URL' and 'MAIN_PAGE_URL' variables!**")
    print("**Also, ensure 'Allow Remote Automation' is enabled in Safari's Develop menu.**")
    print("---------------------------------------")

    if BASE_URL == 'YOUR_ACTUAL_BASE_WEBSITE_URL_HERE' or MAIN_PAGE_URL.endswith('your_members_list_path_here'):
        print("WARNING: Please update the 'BASE_URL' and 'MAIN_PAGE_URL' variables with the actual website URLs.")
        print("Exiting as placeholder URLs are used.")
    else:
        categorized_members_info = scrape_categorized_members()
        if categorized_members_info:
            print("\n--- Summary of Extracted Data ---")
            print(f"Total unique member entries found: {len(categorized_members_info)}")
        else:
            print("No member information extracted.")