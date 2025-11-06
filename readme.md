# 💼 CFO AI Assistant

An intelligent AI-powered assistant for Chief Financial Officers that combines **SQL analysis**, **RAG (Retrieval-Augmented Generation)** for policy documents, and **web search** capabilities in a unified interface.

## 🎯 Features

### 1. **Text-to-SQL Analysis** 
- Natural language queries to SQL database
- Financial metrics and KPIs (profit margins, ROE, ROA, debt ratios)
- Company performance comparisons
- Automated visualizations

### 2. **Policy Document Search (RAG)**
- Semantic search through company policies
- Revenue recognition, expense approvals, investment guidelines
- Compliance and control procedures
- Cited sources for transparency

### 3. **Web Search Integration**
- Real-time market insights
- Current financial trends
- Regulatory updates
- Competitor intelligence

### 4. **Intelligent Query Routing**
- Automatically routes queries to the appropriate agent
- Can be manually overridden
- Seamless multi-agent orchestration

## 🏗️ Architecture

```
User Query
    ↓
Query Router (Claude)
    ↓
┌───────────┬────────────┬─────────────┐
│ SQL Agent │ RAG Agent  │ Web Agent   │
└───────────┴────────────┴─────────────┘
    ↓           ↓              ↓
SQLite DB   ChromaDB      Tavily API
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Anthropic API key ([Get it here](https://console.anthropic.com/))
- (Optional) Tavily API key for web search ([Get it here](https://tavily.com/))

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd cfo-ai-assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. **Initialize the database and documents**
```bash
python setup_data.py
```

5. **Setup the vector store (RAG)**
```bash
python -m src.rag_agent
```

6. **Run the Streamlit app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📁 Project Structure

```
cfo-ai-assistant/
├── app.py                      # Streamlit web interface
├── setup_data.py              # Data initialization script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # This file
│
├── src/
│   ├── config.py             # Configuration settings
│   ├── query_router.py       # Query routing logic
│   ├── sql_agent.py          # Text-to-SQL agent
│   ├── rag_agent.py          # RAG for documents
│   ├── web_agent.py          # Web search agent
│   └── orchestrator.py       # Main coordinator
│
├── data/
│   ├── raw/                  # Raw CSV files
│   ├── processed/            # Processed data
│   └── documents/            # Policy documents (TXT)
│
├── database/
│   └── financial.db          # SQLite database
│
└── vectorstore/              # ChromaDB vector store
```

## 💡 Usage Examples

### SQL Queries
```
"Show me the top 10 companies by revenue"
"Compare profit margins between tech and healthcare sectors"
"Which companies have ROE above 20%?"
"What's the average debt-to-equity ratio?"
```

### Policy Questions (RAG)
```
"What's the approval process for expenses over $10,000?"
"How should we recognize revenue from multi-year contracts?"
"What are our investment policy restrictions?"
"What's the travel policy for international trips?"
```

### Web Research
```
"What are the latest trends in CFO priorities?"
"Recent changes in GAAP standards"
"Current inflation impact on corporate finance"
"What are competitors doing with AI investments?"
```

## 🔧 Customization

### Adding Your Own Data

**Financial Data:**
1. Replace CSV files in `data/raw/`
2. Update `setup_data.py` to match your schema
3. Re-run `python setup_data.py`

**Policy Documents:**
1. Add `.txt` files to `data/documents/`
2. Re-run `python -m src.rag_agent`

### Using Real Kaggle Datasets

Download financial datasets from Kaggle:
```bash
# Install Kaggle CLI
pip install kaggle

# Configure Kaggle API (add credentials to ~/.kaggle/kaggle.json)

# Download a dataset (example)
kaggle datasets download -d <dataset-name>
```

Recommended datasets:
- [Financial Sheets Dataset](https://www.kaggle.com/datasets)
- [SEC EDGAR Company Facts](https://www.kaggle.com/datasets)

## 🌐 Deployment

### Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets (ANTHROPIC_API_KEY) in settings
5. Deploy!

### Docker (Alternative)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python setup_data.py
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t cfo-assistant .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key cfo-assistant
```

## 🧪 Testing

Test individual components:

```bash
# Test SQL Agent
python -m src.sql_agent

# Test RAG Agent
python -m src.rag_agent

# Test Web Agent
python -m src.web_agent

# Test Query Router
python -m src.query_router

# Test Full Orchestrator (CLI mode)
python -m src.orchestrator
```

## 🛠️ Tech Stack

- **LLM**: Claude Sonnet 4 (Anthropic)
- **Orchestration**: LangChain
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers
- **Database**: SQLite
- **Web Search**: Tavily API
- **Frontend**: Streamlit
- **Visualization**: Plotly

## 📊 Sample Database Schema

**companies**
- company_id, company_name, sector, market_cap_billions

**financial_statements**
- company_id, year, quarter, revenue_millions, cost_of_revenue_millions, operating_expenses_millions, net_income_millions, total_assets_millions, total_liabilities_millions, shareholders_equity_millions

**financial_ratios**
- company_id, year, quarter, gross_margin, net_profit_margin, roe, roa, debt_to_equity, current_ratio, quick_ratio


## 🙋 Support

For issues or questions:
1. Check existing issues
2. Create a new issue with details
3. Tag appropriately (bug, feature, question)

## 🎓 Learning Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [RAG Tutorial](https://www.anthropic.com/index/contextual-retrieval)
- [ChromaDB Guide](https://docs.trychroma.com/)

---

**Built using Claude (Anthropic), LangChain, and Streamlit**
