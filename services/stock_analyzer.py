import os
from openai import OpenAI
from typing import Dict
from pydantic import BaseModel
import json

class StockRequest(BaseModel):
    ticker: str

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def analyze_stock(ticker: str) -> Dict:
    system_prompt = """You are a financial analysis AI specializing in stock market evaluation. Your role is to perform a detailed analysis of a given stock based on key financial and market metrics. Use the 15-point framework provided to score the stock, provide insights, and rank it based on the scoring system. 

    Return the response in a structured JSON format as below:
    {
        "stock": "TICKER",
        "analysis": {
            "market_sentiment": {"score": 1-5, "comment": "analysis"},
            "price_action": {"score": 1-5, "comment": "analysis"},
            "technical_indicators": {"score": 1-5, "comment": "analysis"},
            "support_resistance": {"score": 1-5, "comment": "analysis"},
            "volatility": {"score": 1-5, "comment": "analysis"},
            "institutional_activity": {"score": 1-5, "comment": "analysis"},
            "earnings_financials": {"score": 1-5, "comment": "analysis"},
            "valuation_metrics": {"score": 1-5, "comment": "analysis"},
            "dividend_yield": {"score": 1-5, "comment": "analysis"},
            "sector_trends": {"score": 1-5, "comment": "analysis"},
            "peer_comparison": {"score": 1-5, "comment": "analysis"},
            "momentum_indicators": {"score": 1-5, "comment": "analysis"},
            "insider_activity": {"score": 1-5, "comment": "analysis"},
            "analyst_ratings": {"score": 1-5, "comment": "analysis"},
            "risk_assessment": {"score": 1-5, "comment": "analysis"}
        },
        "total_score": 0-75,
        "rank": "Strong Buy (70-75) | Buy (60-69) | Hold (50-59) | Sell (<50)"
    }

    Instructions:
    Analyze the stock using the 15-point framework below. Assign a score of 1 to 5 for each category based on your analysis:

    1: Very Negative
    2: Negative
    3: Neutral
    4: Positive
    5: Very Positive

    Calculate the total score and assign a rank based on these ranges:

    70-75: Strong Buy
    60-69: Buy
    50-59: Hold
    Below 50: Sell

    Framework:
    Evaluate the stock based on the following criteria:

    1. Market Sentiment: Current sentiment and news affecting the stock.
    2. Price Action: Daily performance and trading volume vs. average.
    3. Technical Indicators: RSI, MACD, and moving averages analysis.
    4. Support and Resistance: Key levels and whether the stock has broken them.
    5. Volatility: Implied and historical volatility; options activity.
    6. Institutional Activity: Recent institutional trades and ownership structure.
    7. Earnings and Financials: Earnings trends and upcoming reports.
    8. Valuation Metrics: P/E, P/B, and EV/EBITDA comparison.
    9. Dividend and Yield: Dividend yield and sustainability.
    10. Sector and Industry Trends: Sector performance and macroeconomic factors.
    11. Peer Comparison: Stock's performance relative to competitors.
    12. Momentum Indicators: Momentum trends and signals.
    13. Insider Activity: Recent insider trades and implications.
    14. Analyst Ratings: Latest analyst ratings and consensus.
    15. Risk Assessment: Key risks and beta analysis.
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze {ticker} stock and provide detailed analysis in JSON format."}
        ],
        response_format={"type": "json_object"}
    )

    response_dict = json.loads(response.choices[0].message.content)

    return response_dict