#%%
"""
Text-to-SQL Agent
Converts natural language to SQL queries and executes them
"""
import sqlite3
import pandas as pd
from anthropic import Anthropic
from src.config import Config

class SQLAgent:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.db_path = Config.DATABASE_PATH
        self.schema = self._get_schema()
        
    def _get_schema(self):
        """Get database schema for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema_info = []
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            col_info = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
            schema_info.append(f"\nTable: {table_name}\nColumns: {col_info}")
        
        conn.close()
        return "\n".join(schema_info)
    
    def _generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question"""
        
        prompt = f"""You are an expert SQL query generator for a financial database. 
        
Database Schema:
{self.schema}

User Question: {question}

Generate a valid SQLite query to answer this question. Follow these rules:
1. Return ONLY the SQL query, no explanations
2. Use proper SQLite syntax
3. Include appropriate JOINs if multiple tables are needed
4. Use meaningful column aliases for better readability
5. Add LIMIT clause if the result set might be large (default LIMIT 100)
6. For calculations, use ROUND() for decimal places

SQL Query:"""

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sql_query = response.content[0].text.strip()
        
        # Clean up the query (remove markdown code blocks if present)
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n", 1)[1]
            sql_query = sql_query.rsplit("```", 1)[0]
        
        sql_query = sql_query.strip().rstrip(";")
        
        return sql_query
    
    def _execute_query(self, sql_query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(sql_query, conn)
            return df
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")
        finally:
            conn.close()
    
    def _format_results(self, df: pd.DataFrame, question: str) -> str:
        """Format query results into natural language response"""
        
        if df.empty:
            return "No results found for your query."
        
        # Convert DataFrame to string representation
        df_string = df.to_string(index=False)
        
        prompt = f"""You are a financial analyst assistant. A user asked a question and we retrieved data from the database.

User Question: {question}

Query Results:
{df_string}

Provide a clear, concise answer to the user's question based on these results. Include:
1. A direct answer to their question
2. Key numbers and insights
3. Present data in a clean format (use tables if showing multiple rows)

Keep your response professional and CFO-appropriate."""

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def query(self, question: str) -> dict:
        """
        Main method to process natural language question
        Returns dict with: answer, sql_query, dataframe, error
        """
        try:
            # Generate SQL
            sql_query = self._generate_sql(question)
            
            # Execute query
            df = self._execute_query(sql_query)
            
            # Format results
            answer = self._format_results(df, question)
            
            return {
                "answer": answer,
                "sql_query": sql_query,
                "dataframe": df,
                "error": None
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "sql_query": None,
                "dataframe": None,
                "error": str(e)
            }


# Test function
def test_sql_agent():
    agent = SQLAgent()
    
    test_questions = [
        "Show me the top 5 companies by revenue",
        "What is the average profit margin across all companies?",
        "Which companies have ROE above 20%?",
        "Compare technology sector vs healthcare sector average revenue"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        print('='*60)
        result = agent.query(question)
        print(f"SQL: {result['sql_query']}")
        print(f"\nAnswer:\n{result['answer']}")


if __name__ == "__main__":
    test_sql_agent()
