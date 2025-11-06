"""
Main Orchestrator
Coordinates all agents and handles queries
"""
from src.query_router import QueryRouter
from src.sql_agent import SQLAgent
from src.rag_agent import RAGAgent
from src.web_agent import WebAgent


class CFOAssistant:
    def __init__(self):
        print("Initializing CFO AI Assistant...")
        self.router = QueryRouter()
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
        self.web_agent = WebAgent()
        print("✓ All agents initialized")
    
    def query(self, question: str, force_agent: str = None, use_memory: bool = True) -> dict:
        """
        Process user query and return response
        
        Args:
            question: User's question
            force_agent: Optional - force specific agent ('sql', 'rag', 'web')
            use_memory: Whether to use conversation memory for RAG queries
        
        Returns:
            dict with: answer, agent_used, metadata, error
        """
        
        # Determine which agent to use
        if force_agent:
            agent_type = force_agent.upper()
        else:
            agent_type = self.router.route(question)
        
        print(f"Routing to: {agent_type} agent")
        
        # Route to appropriate agent
        if agent_type == 'SQL':
            result = self.sql_agent.query(question)
            return {
                "answer": result['answer'],
                "agent_used": "SQL Database",
                "metadata": {
                    "sql_query": result.get('sql_query'),
                    "dataframe": result.get('dataframe'),
                },
                "error": result.get('error')
            }
        
        elif agent_type == 'RAG':
            result = self.rag_agent.query(question)
            return {
                "answer": result['answer'],
                "agent_used": "Policy Documents (RAG)",
                "metadata": {
                    "sources": result.get('sources', []),
                    "chunks": result.get('chunks', [])
                },
                "error": result.get('error')
            }
        
        elif agent_type == 'WEB':
            result = self.web_agent.query(question)
            return {
                "answer": result['answer'],
                "agent_used": "Web Search",
                "metadata": {
                    "sources": result.get('sources', []),
                    "search_results": result.get('search_results', [])
                },
                "error": result.get('error')
            }
        
        else:
            return {
                "answer": "I couldn't determine how to handle your query. Please try rephrasing.",
                "agent_used": "None",
                "metadata": {},
                "error": "Unknown agent type"
            }
    
    def chat(self):
        """Interactive chat loop for testing"""
        print("\n" + "="*60)
        print("CFO AI ASSISTANT - Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  'quit' or 'exit' - Exit the assistant")
        print("  'sql: <query>' - Force SQL agent")
        print("  'rag: <query>' - Force RAG agent")
        print("  'web: <query>' - Force web agent")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                # Check for forced agent
                force_agent = None
                if user_input.startswith('sql:'):
                    force_agent = 'sql'
                    user_input = user_input[4:].strip()
                elif user_input.startswith('rag:'):
                    force_agent = 'rag'
                    user_input = user_input[4:].strip()
                elif user_input.startswith('web:'):
                    force_agent = 'web'
                    user_input = user_input[4:].strip()
                
                # Process query
                result = self.query(user_input, force_agent=force_agent)
                
                # Display result
                print(f"\nAgent: {result['agent_used']}")
                print("-" * 60)
                print(result['answer'])
                
                # Show additional metadata
                if result['metadata'].get('sql_query'):
                    print(f"\n[SQL Query: {result['metadata']['sql_query']}]")
                
                if result['metadata'].get('sources'):
                    print(f"\n[Sources: {', '.join(result['metadata']['sources'])}]")
                
                if result.get('error'):
                    print(f"\n⚠ Error: {result['error']}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


# Main entry point
def main():
    assistant = CFOAssistant()
    assistant.chat()


if __name__ == "__main__":
    main()














# """
# Main Orchestrator
# Coordinates all agents and handles queries
# """
# from src.query_router import QueryRouter
# from src.sql_agent import SQLAgent
# from src.rag_agent import RAGAgent
# from src.web_agent import WebAgent


# class CFOAssistant:
#     def __init__(self):
#         print("Initializing CFO AI Assistant...")
#         self.router = QueryRouter()
#         self.sql_agent = SQLAgent()
#         self.rag_agent = RAGAgent()
#         self.web_agent = WebAgent()
#         print("✓ All agents initialized")
    
#     def query(self, question: str, force_agent: str = None) -> dict:
#         """
#         Process user query and return response
        
#         Args:
#             question: User's question
#             force_agent: Optional - force specific agent ('sql', 'rag', 'web')
        
#         Returns:
#             dict with: answer, agent_used, metadata, error
#         """
        
#         # Determine which agent to use
#         if force_agent:
#             agent_type = force_agent.upper()
#         else:
#             agent_type = self.router.route(question)
        
#         print(f"Routing to: {agent_type} agent")
        
#         # Route to appropriate agent
#         if agent_type == 'SQL':
#             result = self.sql_agent.query(question)
#             return {
#                 "answer": result['answer'],
#                 "agent_used": "SQL Database",
#                 "metadata": {
#                     "sql_query": result.get('sql_query'),
#                     "dataframe": result.get('dataframe'),
#                 },
#                 "error": result.get('error')
#             }
        
#         elif agent_type == 'RAG':
#             result = self.rag_agent.query(question)
#             return {
#                 "answer": result['answer'],
#                 "agent_used": "Policy Documents (RAG)",
#                 "metadata": {
#                     "sources": result.get('sources', []),
#                     "chunks": result.get('chunks', [])
#                 },
#                 "error": result.get('error')
#             }
        
#         elif agent_type == 'WEB':
#             result = self.web_agent.query(question)
#             return {
#                 "answer": result['answer'],
#                 "agent_used": "Web Search",
#                 "metadata": {
#                     "sources": result.get('sources', []),
#                     "search_results": result.get('search_results', [])
#                 },
#                 "error": result.get('error')
#             }
        
#         else:
#             return {
#                 "answer": "I couldn't determine how to handle your query. Please try rephrasing.",
#                 "agent_used": "None",
#                 "metadata": {},
#                 "error": "Unknown agent type"
#             }
    
#     def chat(self):
#         """Interactive chat loop for testing"""
#         print("\n" + "="*60)
#         print("CFO AI ASSISTANT - Interactive Mode")
#         print("="*60)
#         print("Commands:")
#         print("  'quit' or 'exit' - Exit the assistant")
#         print("  'sql: <query>' - Force SQL agent")
#         print("  'rag: <query>' - Force RAG agent")
#         print("  'web: <query>' - Force web agent")
#         print("="*60 + "\n")
        
#         while True:
#             try:
#                 user_input = input("\nYou: ").strip()
                
#                 if not user_input:
#                     continue
                
#                 if user_input.lower() in ['quit', 'exit', 'q']:
#                     print("Goodbye!")
#                     break
                
#                 # Check for forced agent
#                 force_agent = None
#                 if user_input.startswith('sql:'):
#                     force_agent = 'sql'
#                     user_input = user_input[4:].strip()
#                 elif user_input.startswith('rag:'):
#                     force_agent = 'rag'
#                     user_input = user_input[4:].strip()
#                 elif user_input.startswith('web:'):
#                     force_agent = 'web'
#                     user_input = user_input[4:].strip()
                
#                 # Process query
#                 result = self.query(user_input, force_agent=force_agent)
                
#                 # Display result
#                 print(f"\nAgent: {result['agent_used']}")
#                 print("-" * 60)
#                 print(result['answer'])
                
#                 # Show additional metadata
#                 if result['metadata'].get('sql_query'):
#                     print(f"\n[SQL Query: {result['metadata']['sql_query']}]")
                
#                 if result['metadata'].get('sources'):
#                     print(f"\n[Sources: {', '.join(result['metadata']['sources'])}]")
                
#                 if result.get('error'):
#                     print(f"\n⚠ Error: {result['error']}")
                
#             except KeyboardInterrupt:
#                 print("\n\nGoodbye!")
#                 break
#             except Exception as e:
#                 print(f"\nError: {e}")


# # Main entry point
# def main():
#     assistant = CFOAssistant()
#     assistant.chat()


# if __name__ == "__main__":
#     main()
