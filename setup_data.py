#%%
"""
Script to download and setup financial dataset
Run this once to prepare your data
"""
import pandas as pd
import sqlite3
from pathlib import Path
from src.config import Config

def create_sample_financial_data():
    """
    Create sample financial dataset with realistic company data
    This simulates what you'd get from Kaggle but ensures you can run immediately
    """
    
    # Sample companies data
    companies_data = {
        'company_id': range(1, 21),
        'company_name': [
            'Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.',
            'Meta Platforms', 'Tesla Inc.', 'NVIDIA Corp.', 'Berkshire Hathaway',
            'JPMorgan Chase', 'Johnson & Johnson', 'Walmart Inc.', 'Visa Inc.',
            'Procter & Gamble', 'Mastercard Inc.', 'UnitedHealth Group', 'Home Depot',
            'Bank of America', 'Pfizer Inc.', 'Coca-Cola Co.', 'PepsiCo Inc.'
        ],
        'sector': [
            'Technology', 'Technology', 'Consumer', 'Technology',
            'Technology', 'Automotive', 'Technology', 'Financial',
            'Financial', 'Healthcare', 'Retail', 'Financial',
            'Consumer', 'Financial', 'Healthcare', 'Retail',
            'Financial', 'Healthcare', 'Consumer', 'Consumer'
        ],
        'market_cap_billions': [
            2800, 2400, 1500, 1700, 800, 650, 1100, 780,
            450, 380, 400, 520, 350, 390, 480, 320,
            280, 260, 270, 240
        ]
    }
    
    # Financial statements data
    financial_data = {
        'company_id': range(1, 21),
        'year': [2024] * 20,
        'quarter': ['Q3'] * 20,
        'revenue_millions': [
            394000, 211000, 575000, 307000, 134000, 96000, 60000, 364000,
            158000, 95000, 611000, 32000, 82000, 25000, 372000, 153000,
            94000, 58000, 46000, 86000
        ],
        'cost_of_revenue_millions': [
            214000, 65000, 356000, 133000, 72000, 79000, 16000, 308000,
            45000, 34000, 463000, 10000, 41000, 8000, 314000, 102000,
            27000, 20000, 18000, 39000
        ],
        'operating_expenses_millions': [
            54000, 56000, 155000, 95000, 42000, 8000, 11000, 22000,
            78000, 28000, 117000, 12000, 24000, 9000, 28000, 25000,
            52000, 25000, 13000, 28000
        ],
        'net_income_millions': [
            100000, 72000, 48000, 61000, 16000, 7200, 26000, 27000,
            28000, 27000, 22000, 8000, 14000, 6500, 24000, 21000,
            12000, 10000, 12000, 15000
        ],
        'total_assets_millions': [
            353000, 411000, 527000, 402000, 229000, 106000, 85000, 1050000,
            3875000, 193000, 252000, 96000, 121000, 82000, 245000, 81000,
            3180000, 226000, 92000, 93000
        ],
        'total_liabilities_millions': [
            290000, 191000, 420000, 124000, 80000, 43000, 26000, 477000,
            3489000, 75000, 163000, 41000, 51000, 40000, 156000, 56000,
            2885000, 136000, 38000, 46000
        ],
        'shareholders_equity_millions': [
            63000, 220000, 107000, 278000, 149000, 63000, 59000, 573000,
            386000, 118000, 89000, 55000, 70000, 42000, 89000, 25000,
            295000, 90000, 54000, 47000
        ]
    }
    
    # Financial ratios (calculated from above)
    ratios_data = {
        'company_id': range(1, 21),
        'year': [2024] * 20,
        'quarter': ['Q3'] * 20,
    }
    
    # Calculate ratios
    revenues = financial_data['revenue_millions']
    costs = financial_data['cost_of_revenue_millions']
    net_incomes = financial_data['net_income_millions']
    assets = financial_data['total_assets_millions']
    liabilities = financial_data['total_liabilities_millions']
    equity = financial_data['shareholders_equity_millions']
    
    ratios_data['gross_margin'] = [round((r - c) / r * 100, 2) if r > 0 else 0 
                                    for r, c in zip(revenues, costs)]
    ratios_data['net_profit_margin'] = [round(ni / r * 100, 2) if r > 0 else 0 
                                         for ni, r in zip(net_incomes, revenues)]
    ratios_data['roe'] = [round(ni / e * 100, 2) if e > 0 else 0 
                          for ni, e in zip(net_incomes, equity)]
    ratios_data['roa'] = [round(ni / a * 100, 2) if a > 0 else 0 
                          for ni, a in zip(net_incomes, assets)]
    ratios_data['debt_to_equity'] = [round(l / e, 2) if e > 0 else 0 
                                      for l, e in zip(liabilities, equity)]
    ratios_data['current_ratio'] = [round(1.2 + (i * 0.1), 2) for i in range(20)]
    ratios_data['quick_ratio'] = [round(0.9 + (i * 0.08), 2) for i in range(20)]
    
    # Create DataFrames
    companies_df = pd.DataFrame(companies_data)
    financial_df = pd.DataFrame(financial_data)
    ratios_df = pd.DataFrame(ratios_data)
    
    return companies_df, financial_df, ratios_df


def setup_database():
    """Create SQLite database and populate with financial data"""
    print("Setting up financial database...")
    
    # Create sample data
    companies_df, financial_df, ratios_df = create_sample_financial_data()
    
    # Save raw data
    companies_df.to_csv(Path(Config.RAW_DATA_DIR) / 'companies.csv', index=False)
    financial_df.to_csv(Path(Config.RAW_DATA_DIR) / 'financial_statements.csv', index=False)
    ratios_df.to_csv(Path(Config.RAW_DATA_DIR) / 'financial_ratios.csv', index=False)
    
    print(f"✓ Saved raw data to {Config.RAW_DATA_DIR}")
    
    # Create database
    conn = sqlite3.connect(Config.DATABASE_PATH)
    
    # Write to database
    companies_df.to_sql('companies', conn, if_exists='replace', index=False)
    financial_df.to_sql('financial_statements', conn, if_exists='replace', index=False)
    ratios_df.to_sql('financial_ratios', conn, if_exists='replace', index=False)
    
    print(f"✓ Created database at {Config.DATABASE_PATH}")
    print(f"  - companies table: {len(companies_df)} rows")
    print(f"  - financial_statements table: {len(financial_df)} rows")
    print(f"  - financial_ratios table: {len(ratios_df)} rows")
    
    conn.close()


def create_sample_policy_documents():
    """Create sample policy documents for RAG"""
    print("\nCreating sample policy documents...")
    
    policies = {
        'Revenue_Recognition_Policy.txt': """
REVENUE RECOGNITION POLICY

Effective Date: January 1, 2024
Document Version: 2.1

1. PURPOSE
This policy establishes guidelines for recognizing revenue in accordance with GAAP and IFRS 15 standards.

2. SCOPE
Applies to all revenue-generating activities across all business units.

3. GENERAL PRINCIPLES
3.1 Revenue is recognized when control of goods or services transfers to the customer.
3.2 Revenue must be measured at the transaction price agreed upon.

4. SPECIFIC SCENARIOS

4.1 Product Sales
- Revenue recognized at point of delivery or shipment (depending on terms)
- FOB shipping point: recognize at shipment
- FOB destination: recognize at delivery

4.2 Multi-Year Contracts
- Revenue from multi-year contracts should be recognized ratably over the contract term
- Upfront fees are deferred and recognized over the service period
- Implementation fees recognized over the expected customer relationship period

4.3 Subscription Services
- Recognized on a straight-line basis over the subscription period
- Monthly subscriptions: recognize monthly
- Annual subscriptions: defer and recognize monthly over 12 months

4.4 Bundled Products and Services
- Allocate transaction price to each performance obligation
- Standalone selling price used for allocation
- Revenue recognized as each obligation is satisfied

5. DOCUMENTATION REQUIREMENTS
All revenue recognition must include:
- Signed contract or purchase order
- Evidence of delivery or service completion
- Collection probability assessment

6. APPROVAL REQUIREMENTS
- Standard transactions: Department head approval
- Non-standard terms: CFO approval required
- Contracts > $1M: CFO and CEO approval required
""",
        
        'Expense_Approval_Policy.txt': """
EXPENSE APPROVAL AND REIMBURSEMENT POLICY

Effective Date: January 1, 2024
Document Version: 3.0

1. PURPOSE
To establish clear guidelines for expense approval, reimbursement, and corporate spending.

2. APPROVAL THRESHOLDS

2.1 Operating Expenses
- Up to $5,000: Department Manager approval
- $5,001 - $10,000: Director approval
- $10,001 - $50,000: VP and CFO approval
- Above $50,000: CFO and Board approval

2.2 Capital Expenditures
- Up to $25,000: VP approval
- $25,001 - $100,000: CFO approval
- Above $100,000: Board approval required

3. TRAVEL AND ENTERTAINMENT

3.1 Domestic Travel
- Flights: Economy class for flights under 4 hours
- Hotels: Standard rate not to exceed $250/night
- Meals: $75/day maximum (excluding client entertainment)

3.2 International Travel
- Flights: Business class allowed for flights over 6 hours
- Hotels: Not to exceed $300/night
- Meals: $100/day maximum

3.3 Client Entertainment
- Reasonable and customary entertainment allowed
- Must have business purpose documented
- Approval required from Director level or above

4. REIMBURSEMENT PROCESS
- Submit expense reports within 30 days
- Include all original receipts
- Processing time: 10 business days
- Payment via direct deposit

5. NON-REIMBURSABLE EXPENSES
- Personal expenses
- Alcohol (except client entertainment)
- Traffic violations
- Spouse/family travel costs
- Entertainment without business purpose
""",
        
        'Financial_Controls_Policy.txt': """
FINANCIAL CONTROLS AND INTERNAL AUDIT POLICY

Effective Date: January 1, 2024
Document Version: 2.0

1. PURPOSE
Establish internal controls to ensure accuracy, prevent fraud, and maintain compliance.

2. SEGREGATION OF DUTIES

2.1 Critical Functions (must be separated)
- Authorization of transactions
- Recording of transactions
- Custody of assets
- Reconciliation activities

2.2 Key Control Points
- No single person controls entire financial transaction
- Dual signatures required for checks over $10,000
- Monthly reconciliations by separate team

3. APPROVAL MATRIX

3.1 Purchase Orders
- <$10,000: Manager approval
- $10,000-$50,000: Director + Finance approval
- >$50,000: VP + CFO approval

3.2 Vendor Payments
- All payments require 3-way match (PO, receipt, invoice)
- ACH payments require dual approval
- Wire transfers require CFO approval

3.3 Payroll
- Department heads approve timesheets
- HR verifies changes
- Finance processes payment
- CFO reviews monthly variance reports

4. BANK RECONCILIATIONS
- Performed monthly within 10 days of month-end
- Reviewed and signed by Finance Manager
- All reconciling items resolved within 30 days

5. FINANCIAL REPORTING CONTROLS
- Monthly close process documented
- Account reconciliations required
- Management review of financial statements
- Variance analysis for budget vs actual >10%

6. FRAUD PREVENTION
- Anonymous hotline for reporting concerns
- Mandatory vacation policy for finance staff
- Regular audit of high-risk areas
- Background checks for finance positions

7. COMPLIANCE REQUIREMENTS
- SOX compliance for internal controls
- Annual external audit
- Quarterly internal audit reviews
- Documentation retention: 7 years minimum
""",
        
        'Investment_Policy.txt': """
CORPORATE INVESTMENT POLICY

Effective Date: January 1, 2024
Document Version: 1.5

1. PURPOSE
Govern the investment of corporate funds to ensure safety, liquidity, and optimal returns.

2. INVESTMENT OBJECTIVES (in order of priority)
2.1 Safety - Preserve capital
2.2 Liquidity - Maintain adequate cash for operations
2.3 Return - Maximize return within acceptable risk parameters

3. AUTHORIZED INVESTMENTS

3.1 Permitted Investments
- Money market funds (AAA rated)
- U.S. Treasury securities
- U.S. Government agency securities
- Certificates of deposit (FDIC insured)
- Commercial paper (A1/P1 rated minimum)
- Corporate bonds (A rated minimum)

3.2 Prohibited Investments
- Derivatives and futures
- Commodities
- Equity securities (except strategic investments)
- Foreign currency speculation
- Cryptocurrency

4. INVESTMENT LIMITS

4.1 Concentration Limits
- Maximum 25% with single issuer (except U.S. Government)
- Maximum 40% in commercial paper
- Maximum 60% in corporate bonds

4.2 Maturity Constraints
- Average portfolio maturity: Maximum 180 days
- No single investment >2 years maturity
- Minimum 20% in overnight or next-day liquidity

5. MINIMUM CREDIT RATINGS
- Money Market Funds: AAA
- Commercial Paper: A1/P1
- Corporate Bonds: A or higher
- Certificates of Deposit: Bank rating A or higher

6. APPROVAL REQUIREMENTS

6.1 Routine Investments (within policy)
- <$5M: Treasurer approval
- $5M-$20M: CFO approval
- >$20M: CFO + CEO approval

6.2 Non-Routine Investments (exceptions to policy)
- Any amount: Board Finance Committee approval

7. REPORTING REQUIREMENTS
- Daily cash position report to CFO
- Weekly investment portfolio summary
- Monthly performance report to Board
- Quarterly compliance certification

8. REVIEW AND REBALANCING
- Portfolio reviewed daily
- Rebalancing as needed to maintain policy compliance
- Annual policy review by Board Finance Committee
"""
    }
    
    # Create policy documents
    for filename, content in policies.items():
        filepath = Path(Config.DOCUMENTS_DIR) / filename
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ Created {filename}")
    
    print(f"✓ Created {len(policies)} policy documents in {Config.DOCUMENTS_DIR}")


if __name__ == "__main__":
    print("=" * 60)
    print("CFO AI ASSISTANT - DATA SETUP")
    print("=" * 60)
    
    # Setup database
    setup_database()
    
    # Create policy documents
    create_sample_policy_documents()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy .env.example to .env")
    print("2. Add your ANTHROPIC_API_KEY to .env")
    print("3. Run: python -m src.rag_agent (to setup vector store)")
    print("4. Run: streamlit run app.py")

# %%
