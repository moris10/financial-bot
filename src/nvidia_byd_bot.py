import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
import telegram

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
STOCKS = ['TSLA.DE', 'BYD', 'NVDA.DE', 'AAPL.DE', 'MSFT.DE', 'GOOGL.DE', 'AMZN.DE']  # Frankfurt exchange for EUR prices where available
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_currency_rate(from_currency='USD', to_currency='EUR'):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url)
        data = response.json()
        return data['rates'][to_currency]
    except Exception as e:
        logging.error(f"Error fetching currency rate: {e}")
        return 1.0

def fetch_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        if data.empty:
            raise ValueError(f"No data for {ticker}")
        return data
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None

def calculate_technical_indicators(data):
    if data is None or data.empty:
        return {}
    rsi = RSIIndicator(close=data['Close']).rsi()
    ma50 = SMAIndicator(close=data['Close'], window=50).sma_indicator()
    ma200 = SMAIndicator(close=data['Close'], window=200).sma_indicator()
    macd = MACD(close=data['Close'])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    recent_low = data['Low'].tail(20).min()
    recent_high = data['High'].tail(20).max()
    if data['Close'].iloc[-1] > ma50.iloc[-1] > ma200.iloc[-1]:
        trend = 'Alta'
    elif data['Close'].iloc[-1] < ma50.iloc[-1] < ma200.iloc[-1]:
        trend = 'Baixa'
    else:
        trend = 'Lateral'
    return {
        'rsi': rsi.iloc[-1],
        'ma50': ma50.iloc[-1],
        'ma200': ma200.iloc[-1],
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'support': recent_low,
        'resistance': recent_high,
        'trend': trend
    }

def analyze_global_trends():
    trends = {
        'IA Generativa': 'Explosão de investimentos em IA, aplicações em saúde e automação.',
        'Veículos Elétricos': 'Transição sustentável, políticas ambientais.',
        'Crescimento da China': 'Expansão econômica.',
        'Energia Sustentável': 'Renováveis em crescimento.',
        'Saúde Digital': 'IA em diagnósticos.',
        'Geopolítica': 'Reconfiguração global.'
    }
    return trends

def emerging_opportunities():
    opportunities = [
        {"trend": "IA em Saúde", "impact": "Diagnósticos", "companies": "MSFT, GOOGL", "opportunity": "Investir antes do boom."},
        {"trend": "EVs Infra", "impact": "Expansão", "companies": "TSLA, BYD", "opportunity": "Infraestrutura."},
        {"trend": "Baterias", "impact": "Energia", "companies": "NVDA, AAPL", "opportunity": "Armazenamento."},
        {"trend": "E-commerce China", "impact": "Consumo", "companies": "AMZN, BYD", "opportunity": "Globalização."}
    ]
    return opportunities

def fetch_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={NEWSAPI_KEY}&language=en"
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])[:5]
        news = []
        for article in articles:
            title = article['title']
            summary = article.get('description', '')
            interpretation = "Notícia geral de mercado; impacto neutro. Conclusão: Manter posições atuais."
            text_lower = (title + summary).lower()
            if 'ai' in text_lower or 'artificial intelligence' in text_lower:
                interpretation = "Relevante para setores de tecnologia como NVDA e MSFT; impacto positivo esperado devido à adoção crescente de IA. Conclusão: Aumento no valor das ações tech."
            elif 'electric vehicle' in text_lower or 'ev' in text_lower:
                interpretation = "Impacta indústria automotiva; oportunidades em TSLA e BYD com expansão de infraestrutura. Conclusão: Crescimento sustentável no setor EVs."
            elif 'china' in text_lower or 'chinese' in text_lower:
                interpretation = "Influencia mercados emergentes e commodities; monitorar impacto em BYD e economia global. Conclusão: Potencial volatilidade em ações chinesas."
            elif 'renewable' in text_lower or 'sustainable' in text_lower:
                interpretation = "Tendência de energia sustentável; benefícios para empresas verdes e NVDA. Conclusão: Investimento em energias limpas como oportunidade de longo prazo."
            elif 'economy' in text_lower or 'fed' in text_lower:
                interpretation = "Notícia econômica; impacto em todos os setores. Conclusão: Monitorar taxas de juros e inflação."
            news.append({
                'title': title,
                'source': article['source']['name'],
                'summary': summary,
                'url': article['url'],
                'interpretation': interpretation
            })
        return news
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

def generate_recommendation(data, indicators, trends, news):
    price = data['Close'].iloc[-1]
    rsi = indicators['rsi']
    trend = indicators['trend']
    if trend == 'Alta' and rsi < 35:
        rec = 'BUY'
        entry_price = price * 0.98
        risk = 'Alto'
        potential = 25
        reasoning = 'Tendência alta, RSI sobrevenda.'
    elif rsi > 70 or trend == 'Baixa':
        rec = 'SELL'
        entry_price = None
        risk = 'Médio'
        potential = -15
        reasoning = 'RSI sobrecomprado ou baixa.'
    else:
        rec = 'HOLD'
        entry_price = price
        risk = 'Baixo'
        potential = 5
        reasoning = 'Estabilidade.'
    target = price * (1 + potential / 100)
    return {
        'recommendation': rec,
        'entry_price': entry_price,
        'target': target,
        'potential': potential,
        'risk': risk,
        'reasoning': reasoning
    }

def generate_report():
    currency_rate = get_currency_rate()
    report = "📊 RELATÓRIO PREDITIVO DE MERCADO\n\n🌍 Visão Global: Mercado em adaptação.\n\n🤖 Tendências:\n"
    trends = analyze_global_trends()
    for k, v in trends.items():
        report += f"- {k}: {v}\n"
    report += "\n🚀 Oportunidades Emergentes:\n"
    opps = emerging_opportunities()
    for opp in opps:
        report += f"- {opp['trend']}: {opp['opportunity']}\n"
    report += "\n📊 Análise Técnica:\n"
    for ticker in STOCKS[:5]:
        data = fetch_stock_data(ticker)
        if data is not None:
            indicators = calculate_technical_indicators(data)
            price_eur = data['Close'].iloc[-1] * currency_rate
            report += f"{ticker} (€{price_eur:.2f}): Tendência {indicators['trend']}, RSI {indicators['rsi']:.2f}\n"
    report += "\n📈 Recomendações:\n"
    for ticker in STOCKS[:5]:
        data = fetch_stock_data(ticker)
        if data is not None:
            indicators = calculate_technical_indicators(data)
            rec = generate_recommendation(data, indicators, trends, [])
            price_eur = data['Close'].iloc[-1] * currency_rate
            entry = f"€{rec['entry_price']:.2f}" if rec['entry_price'] else "N/A"
            report += f"{ticker}: {rec['recommendation']} | Entrada: {entry} | Alvo: €{rec['target']:.2f} | Risco: {rec['risk']}\n"
    report += "\n📰 Notícias:\n"
    news = fetch_news()
    for item in news:
        report += f"- {item['title']} ({item['source']})\n  Interpretação: {item['interpretation']}\n\n"
    report += "💡 Insight: Investir em IA agora.\n"
    return report

async def send_telegram_message(message):
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        logging.info("Message sent to Telegram")
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

async def main():
    try:
        logging.info("Starting financial bot report")
        report = generate_report()
        max_length = 4096
        if len(report) <= max_length:
            await send_telegram_message(report)
        else:
            parts = [report[i:i+max_length] for i in range(0, len(report), max_length)]
            for part in parts:
                await send_telegram_message(part)
                import asyncio
                await asyncio.sleep(0.5)
        logging.info("Report sent successfully")
    except Exception as e:
        logging.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())