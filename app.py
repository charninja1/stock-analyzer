from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import yfinance as yf
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time
import random

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def format_market_cap(market_cap):
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.2f} Trillion"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.2f} Billion"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.2f} Million"
    else:
        return f"${market_cap:,.2f}"

def format_number(num):
    if num is None:
        return "N/A"
    return f"{num:,.2f}"

def calculate_performance(history):
    if history.empty:
        return {"week": "N/A", "month": "N/A"}
    
    current_price = history['Close'].iloc[-1]
    
    week_ago = datetime.now() - timedelta(days=7)
    month_ago = datetime.now() - timedelta(days=30)
    
    week_performance = "N/A"
    month_performance = "N/A"
    
    week_data = history[history.index >= week_ago]
    if not week_data.empty and len(week_data) > 1:
        week_start_price = week_data['Close'].iloc[0]
        week_change = ((current_price - week_start_price) / week_start_price) * 100
        week_performance = f"{week_change:+.2f}%"
    
    month_data = history[history.index >= month_ago]
    if not month_data.empty and len(month_data) > 1:
        month_start_price = month_data['Close'].iloc[0]
        month_change = ((current_price - month_start_price) / month_start_price) * 100
        month_performance = f"{month_change:+.2f}%"
    
    return {"week": week_performance, "month": month_performance}

def get_mock_data(ticker):
    """Fallback mock data for demonstration when APIs are rate limited"""
    mock_companies = {
        "AAPL": {
            "name": "Apple Inc.",
            "price": 182.50,
            "change": 2.35,
            "change_percent": 1.30,
            "pe": 30.5,
            "market_cap": 2.85e12,
            "high_52": 198.23,
            "low_52": 164.08,
            "summary": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
        },
        "MSFT": {
            "name": "Microsoft Corporation",
            "price": 415.20,
            "change": -1.85,
            "change_percent": -0.44,
            "pe": 35.8,
            "market_cap": 3.08e12,
            "high_52": 430.82,
            "low_52": 327.52,
            "summary": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide."
        },
        "GOOGL": {
            "name": "Alphabet Inc.",
            "price": 165.30,
            "change": 3.20,
            "change_percent": 1.97,
            "pe": 26.3,
            "market_cap": 2.05e12,
            "high_52": 175.69,
            "low_52": 121.46,
            "summary": "Alphabet Inc. offers various products and platforms including Google Search, YouTube, Google Cloud, and Android operating system."
        },
        "TSLA": {
            "name": "Tesla, Inc.",
            "price": 245.60,
            "change": -5.40,
            "change_percent": -2.15,
            "pe": 73.2,
            "market_cap": 780e9,
            "high_52": 299.29,
            "low_52": 152.37,
            "summary": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, energy storage systems, and solar panels."
        },
        "NVDA": {
            "name": "NVIDIA Corporation",
            "price": 115.80,
            "change": 4.20,
            "change_percent": 3.76,
            "pe": 65.4,
            "market_cap": 2.86e12,
            "high_52": 140.76,
            "low_52": 39.23,
            "summary": "NVIDIA Corporation provides graphics, computing and networking solutions including GPUs for gaming and professional markets."
        }
    }
    
    if ticker.upper() in mock_companies:
        company = mock_companies[ticker.upper()]
        
        # Generate mock price history
        price_history = []
        base_price = company["price"]
        for i in range(30, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            variation = random.uniform(-5, 5) / 100
            price = base_price * (1 + variation)
            price_history.append({"date": date, "close": price})
        
        return {
            "ticker": ticker.upper(),
            "company_name": company["name"],
            "business_summary": company["summary"],
            "current_price": company["price"],
            "previous_close": company["price"] - company["change"],
            "day_change": company["change"],
            "day_change_percent": company["change_percent"],
            "week_performance": f"{random.uniform(-5, 5):+.2f}%",
            "month_performance": f"{random.uniform(-10, 10):+.2f}%",
            "pe_ratio": company["pe"],
            "forward_pe": company["pe"] * 0.9,
            "market_cap": company["market_cap"],
            "eps": company["price"] / company["pe"],
            "dividend_yield": random.uniform(0, 3) / 100,
            "fifty_two_week_high": company["high_52"],
            "fifty_two_week_low": company["low_52"],
            "volume": random.randint(10000000, 100000000),
            "avg_volume": random.randint(15000000, 80000000),
            "currency": "USD",
            "price_history": price_history,
            "is_mock": True
        }
    return None

def get_stock_data(ticker):
    max_retries = 2
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            if info and 'symbol' in info:
                history = stock.history(period="1mo")
                performance = calculate_performance(history)
                
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                previous_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
                
                day_change = None
                day_change_percent = None
                if current_price and previous_close:
                    day_change = current_price - previous_close
                    day_change_percent = (day_change / previous_close) * 100
                
                stock_data = {
                    "ticker": ticker.upper(),
                    "company_name": info.get('longName', ticker.upper()),
                    "business_summary": info.get('longBusinessSummary', 'No description available'),
                    "current_price": current_price,
                    "previous_close": previous_close,
                    "day_change": day_change,
                    "day_change_percent": day_change_percent,
                    "week_performance": performance["week"],
                    "month_performance": performance["month"],
                    "pe_ratio": info.get('trailingPE'),
                    "forward_pe": info.get('forwardPE'),
                    "market_cap": info.get('marketCap'),
                    "eps": info.get('trailingEps'),
                    "dividend_yield": info.get('dividendYield'),
                    "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                    "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
                    "volume": info.get('volume'),
                    "avg_volume": info.get('averageVolume'),
                    "currency": info.get('financialCurrency', 'USD'),
                    "is_mock": False
                }
                
                price_history = []
                for date, row in history.iterrows():
                    price_history.append({
                        "date": date.strftime('%Y-%m-%d'),
                        "close": row['Close']
                    })
                stock_data["price_history"] = price_history
                
                return stock_data
                
        except Exception as e:
            print(f"Error fetching from yfinance (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    # If yfinance fails, try mock data
    print(f"Using mock data for {ticker} due to API issues")
    return get_mock_data(ticker)

def generate_ai_explanation(stock_data):
    try:
        # If using mock data, provide a disclaimer
        disclaimer = ""
        if stock_data.get('is_mock'):
            disclaimer = "\n\nNote: Due to API rate limiting, this analysis is based on demonstration data."
        
        prompt = f"""You are a financial analyst assistant. Explain the following stock to a beginner investor in a conversational, easy-to-understand way:

Ticker: {stock_data['ticker']}
Company Name: {stock_data['company_name']}
Company Summary: {stock_data['business_summary'][:500]}...

Current Price: ${format_number(stock_data['current_price'])}
Day Change: {f"{stock_data['day_change_percent']:.2f}%" if stock_data['day_change_percent'] else 'N/A'}
Past Week Performance: {stock_data['week_performance']}
Past Month Performance: {stock_data['month_performance']}

P/E Ratio: {format_number(stock_data['pe_ratio']) if stock_data['pe_ratio'] else 'N/A'}
Forward P/E: {format_number(stock_data['forward_pe']) if stock_data['forward_pe'] else 'N/A'}
Market Cap: {format_market_cap(stock_data['market_cap']) if stock_data['market_cap'] else 'N/A'}
EPS: ${format_number(stock_data['eps']) if stock_data['eps'] else 'N/A'}
52-Week Range: ${format_number(stock_data['fifty_two_week_low'])} – ${format_number(stock_data['fifty_two_week_high'])}

Provide:
1. A brief, simple explanation of what the company does (2-3 sentences)
2. How the stock has been performing recently and what that means
3. Whether the stock appears expensive or cheap based on its P/E ratio (explain what P/E means simply)
4. A balanced view with one bullish case and one bearish case
5. End with a reminder that this is for educational purposes only{disclaimer}

Keep the entire response under 250 words and make it sound like you're explaining to a friend who's new to investing."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly financial educator who explains stocks in simple terms."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating AI explanation: {e}")
        # Provide a basic explanation if OpenAI fails
        return f"""**{stock_data['company_name']} ({stock_data['ticker']})**

{stock_data['business_summary'][:200]}...

Current Price: ${format_number(stock_data['current_price'])}
Market Cap: {format_market_cap(stock_data['market_cap']) if stock_data['market_cap'] else 'N/A'}
P/E Ratio: {format_number(stock_data['pe_ratio']) if stock_data['pe_ratio'] else 'N/A'}

The P/E (Price-to-Earnings) ratio helps investors understand if a stock is expensive or cheap relative to its earnings. A higher P/E might mean investors expect growth, while a lower P/E could indicate a value opportunity or concerns about the company.

⚠️ This information is for educational purposes only and should not be considered investment advice. Always do your own research and consult with financial professionals before making investment decisions."""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/explain', methods=['POST'])
def explain_stock():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').strip().upper()
        
        if not ticker:
            return jsonify({"error": "Please provide a stock ticker"}), 400
        
        stock_data = get_stock_data(ticker)
        
        if not stock_data:
            return jsonify({"error": f"Unable to find data for ticker '{ticker}'. Please check the ticker symbol and try again. Potentially also reached rate limits, might have to wait a few hours and try again"}), 404
        
        ai_explanation = generate_ai_explanation(stock_data)
        
        response_data = {
            "ticker": stock_data["ticker"],
            "company_name": stock_data["company_name"],
            "current_price": stock_data["current_price"],
            "day_change": stock_data["day_change"],
            "day_change_percent": stock_data["day_change_percent"],
            "week_performance": stock_data["week_performance"],
            "month_performance": stock_data["month_performance"],
            "pe_ratio": stock_data["pe_ratio"],
            "market_cap": format_market_cap(stock_data["market_cap"]) if stock_data["market_cap"] else "N/A",
            "fifty_two_week_high": stock_data["fifty_two_week_high"],
            "fifty_two_week_low": stock_data["fifty_two_week_low"],
            "price_history": stock_data["price_history"],
            "explanation": ai_explanation,
            "is_mock": stock_data.get("is_mock", False)
        }
        
        # Add a note if using mock data
        if stock_data.get("is_mock"):
            response_data["note"] = "Note: Using demonstration data due to API rate limiting. The analysis is still educational but based on sample data."
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error in explain_stock: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)