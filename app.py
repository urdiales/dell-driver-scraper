import streamlit as st
import json
import os
import base64
from datetime import datetime
import subprocess
import time
from playwright.sync_api import sync_playwright
import pandas as pd
import requests
from PIL import Image
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Dell Driver Scraper",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #007DB8;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #005A8C;
    }
    .logo-container {
        text-align: center;
        padding: 10px;
    }
    .result-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Function to create directories if they don't exist
def create_directories():
    directories = ['data', 'data/json', 'data/markdown', 'logs', 'config']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Create necessary directories
create_directories()

# Load company logo if available
def load_company_logo():
    logo_path = "config/company_logo.png"
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

# Function to upload and save company logo
def upload_company_logo():
    logo_file = st.file_uploader("Upload Company Logo (PNG format recommended)", type=['png', 'jpg', 'jpeg'])
    if logo_file is not None:
        logo_image = Image.open(logo_file)
        logo_image.save("config/company_logo.png")
        st.success("Logo uploaded successfully!")
        return logo_image
    return None

# Function to create download link for files
def get_download_link(file_path, link_text):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
    return href

# Function to scrape Dell drivers
def scrape_dell_drivers(service_tag):
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to Dell support page
            page.goto("https://www.dell.com/support/home/en-us")
            
            # Wait for page to load
            page.wait_for_selector("#inpEntrySelection")
            
            # Enter service tag
            page.fill("#inpEntrySelection", service_tag)
            page.click("button.btn-primary")
            
            # Wait for results page to load
            page.wait_for_load_state("networkidle")
            
            # Check if we're redirected to the product page
            if "drivers" not in page.url:
                # Navigate to drivers page
                drivers_link = page.get_by_role("link", name="Drivers & Downloads")
                if drivers_link:
                    drivers_link.click()
                    page.wait_for_load_state("networkidle")
            
            # Extract product information
            product_info = {}
            product_title_elem = page.query_selector("h1.dds__mb-0")
            if product_title_elem:
                product_info["product_name"] = product_title_elem.inner_text().strip()
            
            # Wait for driver table to load
            page.wait_for_selector(".drivers-table", timeout=30000)
            time.sleep(2)  # Extra wait to ensure everything is loaded
            
            # Extract all drivers
            driver_rows = page.query_selector_all(".drivers-table tbody tr")
            
            for row in driver_rows:
                driver = {}
                
                # Extract driver name
                name_elem = row.query_selector(".driver-name-title")
                if name_elem:
                    driver["name"] = name_elem.inner_text().strip()
                
                # Extract driver category
                category_elem = row.query_selector(".driver-category")
                if category_elem:
                    driver["category"] = category_elem.inner_text().strip()
                
                # Extract driver version
                version_elem = row.query_selector(".driver-version")
                if version_elem:
                    driver["version"] = version_elem.inner_text().strip()
                
                # Extract release date
                date_elem = row.query_selector(".driver-date")
                if date_elem:
                    driver["release_date"] = date_elem.inner_text().strip()
                
                # Extract importance
                importance_elem = row.query_selector(".driver-importance")
                if importance_elem:
                    driver["importance"] = importance_elem.inner_text().strip()
                
                # Extract download link
                download_elem = row.query_selector("a.driver-download-btn")
                if download_elem:
                    driver["download_url"] = download_elem.get_attribute("href")
                    if not driver["download_url"].startswith("http"):
                        driver["download_url"] = "https://www.dell.com" + driver["download_url"]
                
                # Extract description if available
                description_elem = row.query_selector(".driver-description")
                if description_elem:
                    driver["description"] = description_elem.inner_text().strip()
                
                results.append(driver)
            
            browser.close()
    
    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None, None
    
    # Create a timestamp for the file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create JSON output
    output = {
        "service_tag": service_tag,
        "product_info": product_info,
        "timestamp": datetime.now().isoformat(),
        "drivers": results
    }
    
    # Save JSON to file
    json_filename = f"data/json/{service_tag}_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
    
    # Convert to Markdown
    markdown_content = f"# Dell Driver Information for {service_tag}\n\n"
    markdown_content += f"## Product: {product_info.get('product_name', 'Unknown')}\n\n"
    markdown_content += f"**Date Scraped:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown_content += "## Available Drivers\n\n"
    
    for idx, driver in enumerate(results, 1):
        markdown_content += f"### {idx}. {driver.get('name', 'Unknown Driver')}\n\n"
        markdown_content += f"**Category:** {driver.get('category', 'N/A')}\n\n"
        markdown_content += f"**Version:** {driver.get('version', 'N/A')}\n\n"
        markdown_content += f"**Release Date:** {driver.get('release_date', 'N/A')}\n\n"
        markdown_content += f"**Importance:** {driver.get('importance', 'N/A')}\n\n"
        
        if 'description' in driver and driver['description']:
            markdown_content += f"**Description:** {driver.get('description', 'N/A')}\n\n"
        
        if 'download_url' in driver and driver['download_url']:
            markdown_content += f"**Download URL:** [{driver.get('download_url', '#')}]({driver.get('download_url', '#')})\n\n"
        
        markdown_content += "---\n\n"
    
    # Save Markdown to file
    md_filename = f"data/markdown/{service_tag}_{timestamp}.md"
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return json_filename, md_filename

# Function to start Ollama chat
def start_ollama_chat(markdown_file):
    st.session_state.chat_active = True
    st.session_state.chat_file = markdown_file
    st.session_state.messages = []

# Chat function with Ollama
def chat_with_ollama(markdown_file, query):
    try:
        # Read the markdown file content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            context = f.read()
        
        # Prepare the prompt for Ollama
        prompt = f"""
        Context information:
        {context}
        
        User query:
        {query}
        
        Please answer the user query based on the context information provided.
        """
        
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json().get('response', "No response from Ollama")
        else:
            return f"Error: Unable to get response from Ollama. Status code: {response.status_code}"
    
    except Exception as e:
        return f"Error communicating with Ollama: {str(e)}"

# Sidebar for configuration
st.sidebar.title("Dell Driver Scraper")

# Logo section in sidebar
st.sidebar.subheader("Company Branding")
logo_tab1, logo_tab2 = st.sidebar.tabs(["Current Logo", "Upload New Logo"])

with logo_tab1:
    logo = load_company_logo()
    if logo:
        st.image(logo, width=200)
    else:
        st.info("No company logo uploaded. Use the Upload tab to add one.")

with logo_tab2:
    new_logo = upload_company_logo()
    if new_logo:
        st.image(new_logo, width=200)

# Configuration section
st.sidebar.subheader("Configuration")
ollama_server = st.sidebar.text_input("Ollama Server Address", value="http://localhost:11434")
ollama_model = st.sidebar.selectbox("Ollama Model", ["llama3", "mistral", "gemma", "phi3"])

# Main content area
st.title("Dell Driver Scraper")
st.write("Scrape driver information from Dell's support website using a service tag or product ID.")

# Service tag input
service_tag = st.text_input("Enter Dell Service Tag or Product ID (e.g., GPN01Q2)", 
                          help="You can find the service tag on the sticker attached to your Dell product")

# Initialize session state variables if they don't exist
if 'chat_active' not in st.session_state:
    st.session_state.chat_active = False
if 'chat_file' not in st.session_state:
    st.session_state.chat_file = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Scrape button
if st.button("Scrape Driver Information"):
    if service_tag:
        with st.spinner("Scraping Dell support website for driver information..."):
            json_file, md_file = scrape_dell_drivers(service_tag)
            
            if json_file and md_file:
                st.success(f"Successfully scraped driver information for service tag: {service_tag}")
                
                # Display download links
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(get_download_link(json_file, "Download JSON File"), unsafe_allow_html=True)
                with col2:
                    st.markdown(get_download_link(md_file, "Download Markdown File"), unsafe_allow_html=True)
                
                # Display JSON preview
                with st.expander("Preview JSON Data"):
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                    st.json(json_data)
                
                # Display Markdown preview
                with st.expander("Preview Markdown"):
                    with open(md_file, 'r') as f:
                        md_content = f.read()
                    st.markdown(md_content)
                
                # Option to chat with Ollama about the data
                st.subheader("Chat with Ollama about this data")
                if st.button("Start Ollama Chat"):
                    start_ollama_chat(md_file)
            else:
                st.error("Failed to scrape driver information. Please check the service tag and try again.")
    else:
        st.warning("Please enter a service tag or product ID.")

# Chat interface
if st.session_state.chat_active and st.session_state.chat_file:
    st.subheader("Chat with Ollama about Driver Information")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # User input
    user_input = st.chat_input("Ask a question about the drivers...")
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get response from Ollama
        with st.spinner("Ollama is thinking..."):
            ollama_response = chat_with_ollama(st.session_state.chat_file, user_input)
        
        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": ollama_response})
        
        # Display assistant message
        with st.chat_message("assistant"):
            st.write(ollama_response)

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit and Playwright")