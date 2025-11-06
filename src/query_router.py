"""
Query Router
Determines which agent should handle a query
"""
from anthropic import Anthropic
from src.config import Config


class QueryRouter:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    def route(self, query: str) -> str:
        """
        Determine which agent should handle the query
        Returns: 'sql', 'rag', or 'web'
        """
        
        prompt = f"""You are a query routing system for a CFO AI assistant. You must classify the user's query into ONE of these categories:

1. SQL - Questions about financial data, metrics, company performance, numbers
   Examples: 
   - "Show me top 5 companies by revenue"
   - "What is the average profit margin?"
   - "Which companies have debt-to-equity ratio above 2?"
   - "Compare revenue across sectors"

2. RAG - Questions about internal policies, procedures, guidelines, approval processes
   Examples:
   - "What's the approval process for expenses over $10,000?"
   - "How should we recognize revenue from subscriptions?"
   - "What's our travel policy?"
   - "What are the investment restrictions?"

3. WEB - Questions about current events, market trends, external information, competitors
   Examples:
   - "What are current market trends?"
   - "Latest news about inflation"
   - "What are competitors doing?"
   - "Recent regulatory changes"

User Query: {query}

Respond with ONLY ONE WORD: SQL, RAG, or WEB"""

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        route = response.content[0].text.strip().upper()
        
        # Validate and default
        if route not in ['SQL', 'RAG', 'WEB']:
            # Default routing logic
            query_lower = query.lower()
            
            # Check for SQL keywords
            sql_keywords = ['show', 'list', 'compare', 'average', 'sum', 'count', 'revenue', 'profit', 
                           'margin', 'companies', 'ratio', 'financial', 'metric']
            if any(keyword in query_lower for keyword in sql_keywords):
                return 'SQL'
            
            # Check for policy keywords
            policy_keywords = ['policy', 'approval', 'procedure', 'guideline', 'process', 
                              'requirement', 'should we', 'how to', 'recognize']
            if any(keyword in query_lower for keyword in policy_keywords):
                return 'RAG'
            
            # Default to web for everything else
            return 'WEB'
        
        return route


# # Test function
# def test_router():
#     router = QueryRouter()
    
#     test_queries = [
#         ("Show me the top 10 companies by market cap", "SQL"),
#         ("What's our expense approval policy?", "RAG"),
#         ("Latest trends in CFO priorities", "WEB"),
#         ("Compare profit margins across sectors", "SQL"),
#         ("How do we recognize revenue from multi-year contracts?", "RAG"),
#         ("What are competitors investing in AI?", "WEB"),
#     ]
    
#     print("Testing Query Router")
#     print("="*60)
    
#     correct = 0
#     for query, expected in test_queries:
#         result = router.route(query)
#         status = "✓" if result == expected else "✗"
#         print(f"{status} Query: {query}")
#         print(f"  Expected: {expected}, Got: {result}\n")
#         if result == expected:
#             correct += 1
    
#     print(f"Accuracy: {correct}/{len(test_queries)} ({correct/len(test_queries)*100:.1f}%)")


# if __name__ == "__main__":
#     test_router()
