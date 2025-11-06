"""
Web Search Agent
Searches the internet for current information
"""
from anthropic import Anthropic
from src.config import Config

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class WebAgent:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        # Initialize Tavily if available
        if TAVILY_AVAILABLE and Config.TAVILY_API_KEY:
            self.tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
            self.search_enabled = True
        else:
            self.tavily = None
            self.search_enabled = False
    
    def _search_web(self, query: str, max_results: int = 5) -> list:
        """Perform web search using Tavily"""
        if not self.search_enabled:
            return []
        
        try:
            response = self.tavily.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            return response.get('results', [])
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _format_search_results(self, results: list) -> str:
        """Format search results into readable context"""
        if not results:
            return "No search results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"[{i}] {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Content: {result.get('content', 'No content')}\n"
            )
        
        return "\n".join(formatted)
    
    def query(self, question: str) -> dict:
        """
        Search web and answer question
        Returns dict with: answer, sources, search_results, error
        """
        if not self.search_enabled:
            return {
                "answer": "Web search is not configured. Please add TAVILY_API_KEY to your .env file. You can get a free API key at https://tavily.com",
                "sources": [],
                "search_results": [],
                "error": "Web search not configured"
            }
        
        try:
            # Perform web search
            search_results = self._search_web(question)
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information on the web for your query.",
                    "sources": [],
                    "search_results": [],
                    "error": None
                }
            
            # Format search results as context
            context = self._format_search_results(search_results)
            
            # Generate answer with Claude
            prompt = f"""You are a helpful financial research assistant. Answer the user's question based on the web search results provided.

Web Search Results:
{context}

User Question: {question}

Instructions:
1. Provide a clear, concise answer based on the search results
2. Cite sources using [1], [2], etc. format
3. Focus on the most relevant and recent information
4. If information is conflicting, mention different perspectives
5. Be objective and factual

Answer:"""

            response = self.client.messages.create(
                model=Config.ANTHROPIC_MODEL,
                max_tokens=2048,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text
            
            # Extract sources
            sources = [
                {"title": r.get('title'), "url": r.get('url')}
                for r in search_results
            ]
            
            return {
                "answer": answer,
                "sources": sources,
                "search_results": search_results,
                "error": None
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error while searching: {str(e)}",
                "sources": [],
                "search_results": [],
                "error": str(e)
            }


# Test function
def test_web_agent():
    agent = WebAgent()
    
    if not agent.search_enabled:
        print("Web search is not configured. Skipping test.")
        print("To enable: Get API key from https://tavily.com and add to .env")
        return
    
    test_questions = [
        "What are the latest trends in CFO priorities for 2024?",
        "Recent changes in GAAP revenue recognition standards",
        "Current inflation impact on corporate finance"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        print('='*60)
        result = agent.query(question)
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources:")
        for source in result['sources']:
            print(f"  - {source['title']}: {source['url']}")


if __name__ == "__main__":
    test_web_agent()
