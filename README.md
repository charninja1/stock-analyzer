# Stock Analyzer - AI-Powered Stock Insights

A complete web application that provides AI-powered stock analysis using real-time data from Yahoo Finance and OpenAI GPT-4. Created with help from claude.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   ./run.sh
   # OR
   python3 app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5001`

## Features

- **Real-time Stock Data**: Fetches current prices, metrics, and historical data from Yahoo Finance
- **AI-Powered Analysis**: GPT-4 generates beginner-friendly explanations of stocks
- **Comprehensive Metrics**: P/E ratio, market cap, 52-week range, performance tracking
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Graceful handling of invalid tickers and API errors

## Project Structure

```
stocker/
├── app.py               # Flask backend with API endpoints
├── requirements.txt     # Python dependencies
├── run.sh              # Startup script
├── .env                # Environment variables (API keys)
├── templates/
│   └── index.html      # Frontend HTML
└── static/
    └── style.css       # Styling
```

## Configuration

The app requires an OpenAI API key in the `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/explain` - Get stock analysis
  - Body: `{"ticker": "AAPL"}`
  - Returns: Stock data with AI explanation

## Important Notes

- **Port**: The app runs on port 5001 (changed from 5000 to avoid macOS AirPlay conflict)
- **Rate Limiting**: Yahoo Finance may rate limit requests during heavy usage
- **API Costs**: Each analysis uses OpenAI GPT-4 tokens
- **Educational Purpose**: This tool is for educational purposes only, not financial advice

## Troubleshooting

If you encounter a "Too Many Requests" error:
- Wait a few minutes before trying again
- Yahoo Finance has rate limits on free API access

If port 5001 is in use:
- Edit `app.py` line 199 to change the port number
- Update `run.sh` accordingly

## License

For educational purposes only. Not financial advice.
