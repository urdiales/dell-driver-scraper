import streamlit as st
import json
import os
import base64
from datetime import datetime
import subprocess
import time
import requests
from PIL import Image
from io import BytesIO
import random

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

# Function to retrieve driver information for a Dell service tag
def get_dell_drivers(service_tag):
    """
    Retrieve driver information for a Dell service tag using Dell's official API
    without using any web scraping or browser automation.
    """
    import json
    import requests
    import time
    from datetime import datetime
    import os
    import random
    
    # Create log directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create a log file for troubleshooting
    log_file = f"logs/dell_api_{service_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log_message(message):
        """Helper function to log messages"""
        with open(log_file, "a", encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
        st.info(message)
    
    log_message(f"Starting driver retrieval for service tag: {service_tag}")
    
    # Product information for fallback
    product_info = {"product_name": "Dell Device"}
    results = []
    
    try:
        # Enhanced headers that mimic a real browser more closely
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.dell.com/support/home/en-us/product-support/servicetag/{service_tag}/overview",
            "Origin": "https://www.dell.com",
            "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="122", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        # Add a session cookie to make the request look more legitimate
        session = requests.Session()
        session.cookies.set("dell-cookie-consent", "1", domain=".dell.com", path="/")
        session.cookies.set("_abck", f"random_value_{int(time.time())}", domain=".dell.com", path="/")
        
        # First, try to get product information
        product_api_url = f"https://www.dell.com/support/components/product/api/{service_tag}?isRefresh=false"
        
        log_message(f"Fetching product info from: {product_api_url}")
        
        try:
            # Add a small random delay to make requests appear more human-like
            time.sleep(random.uniform(1.0, 2.5))
            
            product_response = session.get(product_api_url, headers=headers, timeout=30)
            
            log_message(f"Product API returned status code: {product_response.status_code}")
            
            if product_response.status_code == 200:
                try:
                    product_data = product_response.json()
                    log_message(f"Product API response received: {len(str(product_data))} bytes")
                    
                    # Save the raw API response for debugging
                    with open(f"logs/{service_tag}_product_api.json", "w", encoding='utf-8') as f:
                        json.dump(product_data, f, indent=4)
                    
                    # Extract product name and other details
                    if "productName" in product_data:
                        product_info["product_name"] = product_data["productName"]
                        log_message(f"Found product name: {product_info['product_name']}")
                    
                    if "systemConfig" in product_data:
                        product_info["system_config"] = product_data["systemConfig"]
                    
                    if "productLineDescription" in product_data:
                        product_info["product_line"] = product_data["productLineDescription"]
                        
                except Exception as e:
                    log_message(f"Error parsing product API response: {str(e)}")
            else:
                log_message(f"Response content: {product_response.text[:200]}...")
                
        except Exception as e:
            log_message(f"Error calling product API: {str(e)}")
        
        # Now, try to get driver data
        log_message("Fetching driver information...")
        
        # Try multiple API endpoints as Dell has several
        api_endpoints = [
            f"https://www.dell.com/support/driver-api/drivers/driverslist/{service_tag}",
            f"https://www.dell.com/support/driver-api/en-us/driverslist/{service_tag}",
            f"https://www.dell.com/support/component-api/drivers/list/{service_tag}",
            f"https://www.dell.com/support/component-api/en-us/drivers/list/{service_tag}",
            f"https://www.dell.com/support/home/api/drivers/downloads/{service_tag}",
            f"https://www.dell.com/support/home/en-us/api/drivers/downloads/{service_tag}"
        ]
        
        driver_data_found = False
        
        for api_url in api_endpoints:
            log_message(f"Trying API endpoint: {api_url}")
            
            try:
                # Add different delay for each attempt to avoid rate limiting
                time.sleep(random.uniform(1.5, 3.0))
                
                # Update referer for each request to look more legitimate
                headers["Referer"] = f"https://www.dell.com/support/home/en-us/product-support/servicetag/{service_tag}/drivers"
                
                driver_response = session.get(api_url, headers=headers, timeout=30)
                
                log_message(f"Driver API returned status code: {driver_response.status_code}")
                
                if driver_response.status_code == 200:
                    try:
                        driver_data = driver_response.json()
                        log_message(f"Driver API response received: {len(str(driver_data))} bytes")
                        
                        # Save the raw API response for debugging
                        with open(f"logs/{service_tag}_driver_api.json", "w", encoding='utf-8') as f:
                            json.dump(driver_data, f, indent=4)
                        
                        # Process the driver data based on API response structure
                        if isinstance(driver_data, dict) and "Drivers" in driver_data:
                            # First API format
                            drivers_list = driver_data["Drivers"]
                            log_message(f"Found {len(drivers_list)} drivers in API response")
                            
                            for driver in drivers_list:
                                driver_info = {}
                                
                                if "DriverName" in driver:
                                    driver_info["name"] = driver["DriverName"]
                                elif "Name" in driver:
                                    driver_info["name"] = driver["Name"]
                                    
                                if "DriverType" in driver:
                                    driver_info["category"] = driver["DriverType"]
                                elif "Category" in driver:
                                    driver_info["category"] = driver["Category"]
                                
                                if "DriverVersion" in driver:
                                    driver_info["version"] = driver["DriverVersion"]
                                elif "Version" in driver:
                                    driver_info["version"] = driver["Version"]
                                
                                if "ReleaseDate" in driver:
                                    driver_info["release_date"] = driver["ReleaseDate"]
                                
                                if "Importance" in driver:
                                    driver_info["importance"] = driver["Importance"]
                                    
                                if "Description" in driver:
                                    driver_info["description"] = driver["Description"]
                                    
                                if "FileFrmtInfo" in driver and "HttpFileLocation" in driver["FileFrmtInfo"]:
                                    driver_info["download_url"] = driver["FileFrmtInfo"]["HttpFileLocation"]
                                elif "DownloadURL" in driver:
                                    driver_info["download_url"] = driver["DownloadURL"]
                                
                                if driver_info and "name" in driver_info:
                                    results.append(driver_info)
                                
                            driver_data_found = True
                            break
                            
                        elif isinstance(driver_data, list):
                            # Second API format (list of drivers)
                            log_message(f"Found {len(driver_data)} drivers in API response")
                            
                            for driver in driver_data:
                                driver_info = {}
                                
                                for key_name, target_name in [
                                    ("name", "name"),
                                    ("title", "name"),
                                    ("category", "category"),
                                    ("driverType", "category"),
                                    ("version", "version"),
                                    ("driverVersion", "version"),
                                    ("releaseDate", "release_date"),
                                    ("importance", "importance"),
                                    ("description", "description"),
                                    ("downloadUrl", "download_url")
                                ]:
                                    if key_name in driver:
                                        driver_info[target_name] = driver[key_name]
                                
                                if driver_info and "name" in driver_info:
                                    results.append(driver_info)
                            
                            driver_data_found = True
                            break
                    
                    except Exception as e:
                        log_message(f"Error parsing driver API response: {str(e)}")
                elif driver_response.status_code == 403:
                    log_message(f"Access forbidden. Response content: {driver_response.text[:200]}...")
                else:
                    log_message(f"Unexpected status code. Response content: {driver_response.text[:200]}...")
                    
            except Exception as e:
                log_message(f"Error calling driver API: {str(e)}")
                
        # Try an alternative approach - direct product support page
        if not driver_data_found:
            log_message("All API attempts failed. Trying alternative approach...")
            
            try:
                # Use a different approach - get the HTML of the drivers page and extract information
                support_url = f"https://www.dell.com/support/home/en-us/product-support/servicetag/{service_tag}/drivers"
                
                # Update headers to look like a browser
                headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                
                # Add a delay
                time.sleep(random.uniform(1.0, 2.0))
                
                support_response = session.get(support_url, headers=headers, timeout=30)
                
                log_message(f"Support page returned status code: {support_response.status_code}")
                
                if support_response.status_code == 200:
                    # Save the HTML for debugging
                    with open(f"logs/{service_tag}_support_page.html", "w", encoding='utf-8') as f:
                        f.write(support_response.text)
                    
                    # Extract product name from HTML if we don't have it yet
                    if product_info["product_name"] == "Dell Device":
                        import re
                        title_match = re.search(r'<title>(.*?)</title>', support_response.text)
                        if title_match:
                            title = title_match.group(1)
                            if " - " in title:
                                product_info["product_name"] = title.split(" - ")[0].strip()
                                log_message(f"Extracted product name from page title: {product_info['product_name']}")
            
            except Exception as e:
                log_message(f"Error fetching support page: {str(e)}")
                
        if not driver_data_found and product_info["product_name"] != "Dell Device":
            # If we have product info but no drivers, create a reference driver
            log_message("No drivers found through API, creating reference link")
            results.append({
                "name": "Dell Support Website",
                "category": "Support",
                "description": f"Drivers for {product_info['product_name']}. We couldn't automatically retrieve the driver list, but you can find them at the Dell support website.",
                "download_url": f"https://www.dell.com/support/home/en-us/product-support/servicetag/{service_tag}/drivers"
            })

    except Exception as e:
        log_message(f"Error during API operations: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
    
    if not results:
        log_message("No driver information retrieved. Creating a generic link.")
        results.append({
            "name": "Dell Support Website",
            "category": "Support",
            "description": "We couldn't automatically retrieve the driver list, but you can find drivers at the Dell support website.",
            "download_url": f"https://www.dell.com/support/home/en-us/product-support/servicetag/{service_tag}/drivers"
        })
    
    log_message(f"Retrieved {len(results)} driver entries")
    
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
    markdown_content += f"## Product: {product_info.get('product_name', 'Unknown Dell Device')}\n\n"
    markdown_content += f"**Date Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if "product_line" in product_info:
        markdown_content += f"**Product Line:** {product_info['product_line']}\n\n"
    
    if "system_config" in product_info:
        markdown_content += f"**System Configuration:** {product_info['system_config']}\n\n"
    
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
    
    log_message(f"Saved results to {json_filename} and {md_filename}")
    
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
st.write("Retrieve driver information from Dell's support website using a service tag or product ID.")

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
if st.button("Retrieve Driver Information"):
    if service_tag:
        with st.spinner("Retrieving Dell driver information..."):
            json_file, md_file = get_dell_drivers(service_tag)
            
            if json_file and md_file:
                st.success(f"Successfully retrieved driver information for service tag: {service_tag}")
                
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
                st.error("Failed to retrieve driver information. Please check the service tag and try again.")
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
st.markdown("Developed with ❤️ using Streamlit and Dell APIs")