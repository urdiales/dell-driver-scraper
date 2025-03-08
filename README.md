# Dell Driver Scraper

A professional application to scrape driver information from Dell's support website using a service tag or product ID. The application provides a user-friendly interface to view and download driver information as JSON and Markdown files, and allows chatting with the data using Ollama.

## Features

- Clean, professional user interface with company logo support
- Scrape driver information using Dell service tags
- Export results in JSON and Markdown formats
- Chat with the data using Ollama AI
- Easy deployment with Docker and Docker Compose
- Compatible with Portainer and Dockge for simplified management

## Screenshots

![Dell Driver Scraper Screenshot](https://place-hold.it/800x500&text=Dell%20Driver%20Scraper)

## Quick Start (3-Step Deployment)

### Step 1: Clone the Repository

```bash
git clone https://github.com/urdiales/dell-driver-scraper.git
cd dell-driver-scraper
```

### Step 2: Start the Application

```bash
docker compose up -d
```

After the containers are running, initialize the Ollama model:

```bash
chmod +x init-ollama.sh
./init-ollama.sh
```

This will download the Llama3 model (approximately 4GB) to enable AI chat functionality.

### Step 3: Access the Application

Open your web browser and navigate to:
```
http://localhost:8501
```

That's it! The application is now running and ready to use.

### Video Walkthrough

[![Dell Driver Scraper Setup Tutorial](https://place-hold.it/500x300&text=Dell%20Driver%20Scraper%20Tutorial)](https://example.com/video-tutorial)

## Detailed Setup Instructions

### Prerequisites

- Docker and Docker Compose installed on your system
- Internet connection to download Docker images and Dell driver information

### Configuration Options

You can customize the application by:

1. Adding a company logo through the web interface
2. Changing the Ollama model in the sidebar

### Running with Portainer

If you prefer to use Portainer for container management:

1. Make sure Portainer is installed and running
2. Navigate to your Portainer instance (typically at http://localhost:9000)
3. Go to Stacks → Add stack
4. Copy and paste the contents of the docker-compose.yml file
5. Deploy the stack

### Running with Dockge

If you prefer to use Dockge for stack management:

1. Make sure Dockge is installed and running
2. Navigate to your Dockge instance (typically at http://localhost:5001)
3. Click "Create Stack"
4. Upload or copy the docker-compose.yml file
5. Deploy the stack

## Usage Guide

1. Enter a Dell service tag or product ID in the input field (e.g., GPN01Q2)
2. Click "Scrape Driver Information"
3. Wait for the scraping process to complete
4. View the results and download JSON or Markdown files
5. Click "Start Ollama Chat" to ask questions about the driver information

## Project Structure

```
dell-driver-scraper/
├── app.py                   # Main Streamlit application
├── Dockerfile               # Container definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
├── config/                  # Configuration files
│   └── company_logo.png     # Custom company logo (if uploaded)
├── data/                    # Scraped data storage
│   ├── json/                # JSON output files
│   └── markdown/            # Markdown output files
└── logs/                    # Application logs
```

## Troubleshooting

- **Application not starting**: Check Docker logs with `docker compose logs`
- **Scraping errors**: Verify the service tag is correct and try again
- **Ollama not responding**: Ensure the Ollama container is running with `docker ps`

## Technical Details

- Backend: Python with Streamlit and Playwright
- AI Integration: Ollama API
- Data Formats: JSON and Markdown
- Deployment: Docker and Docker Compose

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For help and questions, please open an issue on the GitHub repository:
https://github.com/urdiales/dell-driver-scraper/issues