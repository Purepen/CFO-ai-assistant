"""
Streamlit Web Interface for CFO AI Assistant
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.orchestrator import CFOAssistant
from src.config import Config

# Page config
st.set_page_config(
    page_title="CFO AI Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .sql-badge {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .rag-badge {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .web-badge {
        background-color: #e8f5e9;
        color: #388e3c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assistant' not in st.session_state:
    with st.spinner("Initializing CFO AI Assistant..."):
        st.session_state.assistant = CFOAssistant()
    st.success("✓ Assistant initialized!")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar
with st.sidebar:
    st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4bc.png", width=80)
    st.title("CFO AI Assistant")
    st.markdown("---")
    
    st.subheader("🎯 Capabilities")
    st.markdown("""
    - 📊 **SQL Analysis**: Query financial data and metrics
    - 📋 **Policy Search**: Find company policies and procedures
    - 🌐 **Web Research**: Get current market insights
    """)
    
    st.markdown("---")
    st.subheader("⚙️ Settings")
    
    # Agent selection
    agent_mode = st.radio(
        "Agent Mode",
        ["Auto (Recommended)", "Force SQL", "Force RAG", "Force Web"],
        help="Auto mode automatically routes queries to the best agent"
    )
    
    # Memory toggle for RAG agent
    use_memory = st.checkbox(
        "🧠 Enable Conversation Memory (RAG only)",
        value=True,
        help="Remember previous questions for context in policy searches"
    )
    
    # Clear memory button
    if use_memory and st.button("🔄 Clear Memory"):
        if hasattr(st.session_state.assistant.rag_agent, 'clear_memory'):
            st.session_state.assistant.rag_agent.clear_memory()
            st.success("Memory cleared!")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    st.subheader("💡 Example Queries")
    
    example_queries = {
        "SQL": [
            "Show top 5 companies by revenue",
            "Compare tech vs healthcare profit margins",
            "Which companies have ROE above 20%?"
        ],
        "RAG": [
            "What's the expense approval policy?",
            "How do we recognize subscription revenue?",
            "What are our investment restrictions?"
        ],
        "Web": [
            "Latest CFO trends in 2024",
            "Current inflation impact on finance",
            "Recent GAAP changes"
        ]
    }
    
    for category, queries in example_queries.items():
        with st.expander(f"{category} Examples"):
            for query in queries:
                if st.button(query, key=f"example_{query}"):
                    st.session_state.current_query = query

# Main content
st.markdown('<div class="main-header">💼 CFO AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your intelligent financial co-pilot for data, policies, and insights</div>', unsafe_allow_html=True)

# Query input
col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input(
        "Ask me anything about financial data, company policies, or market insights:",
        value=st.session_state.get('current_query', ''),
        placeholder="e.g., Show me companies with profit margin above 15%",
        key="query_input"
    )
with col2:
    submit = st.button("🚀 Ask", type="primary", use_container_width=True)

# Process query
if submit and query:
    # Clear the example query
    if 'current_query' in st.session_state:
        del st.session_state.current_query
    
    # Determine force agent
    force_agent = None
    if agent_mode == "Force SQL":
        force_agent = "sql"
    elif agent_mode == "Force RAG":
        force_agent = "rag"
    elif agent_mode == "Force Web":
        force_agent = "web"
    
    # Process query
    with st.spinner("🤔 Processing your query..."):
        result = st.session_state.assistant.query(query, force_agent=force_agent)
    
    # Add to history
    st.session_state.chat_history.append({
        "query": query,
        "result": result
    })

# Display chat history
if st.session_state.chat_history:
    st.markdown("---")
    
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.container():
            # Query
            st.markdown(f"### 💬 You asked:")
            st.info(chat['query'])
            
            # Response
            result = chat['result']
            
            # Agent badge
            agent_class = ""
            if "SQL" in result['agent_used']:
                agent_class = "sql-badge"
            elif "RAG" in result['agent_used']:
                agent_class = "rag-badge"
            elif "Web" in result['agent_used']:
                agent_class = "web-badge"
            
            st.markdown(f'<span class="agent-badge {agent_class}">🤖 {result["agent_used"]}</span>', 
                       unsafe_allow_html=True)
            
            # Answer
            st.markdown(result['answer'])
            
            # Additional metadata
            metadata = result.get('metadata', {})
            
            # SQL-specific display
            if metadata.get('sql_query'):
                with st.expander("🔍 View SQL Query"):
                    st.code(metadata['sql_query'], language='sql')
                
                # Show dataframe if available
                if metadata.get('dataframe') is not None:
                    df = metadata['dataframe']
                    if not df.empty:
                        with st.expander("📊 View Data Table"):
                            st.dataframe(df, use_container_width=True)
                        
                        # Auto-visualization for numeric data
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        if len(numeric_cols) > 0 and len(df) > 1:
                            with st.expander("📈 Visualization"):
                                # Create appropriate chart
                                if len(df) <= 20:  # Bar chart for smaller datasets
                                    if len(numeric_cols) == 1:
                                        fig = px.bar(df, x=df.columns[0], y=numeric_cols[0])
                                    else:
                                        fig = px.bar(df, x=df.columns[0], y=numeric_cols)
                                else:  # Line chart for larger datasets
                                    fig = px.line(df, x=df.columns[0], y=numeric_cols)
                                
                                st.plotly_chart(fig, use_container_width=True)
            
            # RAG-specific display
            if metadata.get('sources'):
                with st.expander("📚 Sources"):
                    for source in metadata['sources']:
                        st.markdown(f"- {source}")
            
            # Web-specific display
            if metadata.get('sources') and isinstance(metadata['sources'], list) and len(metadata['sources']) > 0:
                if isinstance(metadata['sources'][0], dict):  # Web sources
                    with st.expander("🔗 Web Sources"):
                        for source in metadata['sources']:
                            st.markdown(f"- [{source.get('title', 'Source')}]({source.get('url', '#')})")
            
            # Error display
            if result.get('error'):
                st.error(f"⚠️ Error: {result['error']}")
            
            st.markdown("---")

else:
    # Welcome message
    st.markdown("""
    ### 👋 Welcome to CFO AI Assistant!
    
    I can help you with:
    
    1. **📊 Financial Analysis** - Query company data, metrics, and performance
    2. **📋 Policy Information** - Search through company policies and procedures  
    3. **🌐 Market Research** - Get current trends and external insights
    
    **Try asking:**
    - "Show me the top 10 companies by market cap"
    - "What's our expense approval process?"
    - "Latest trends in CFO priorities"
    
    Select an example from the sidebar or type your own question above! 👆
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.875rem;">
    Built with ❤️ using Claude (Anthropic), LangChain, ChromaDB, and Streamlit
</div>
""", unsafe_allow_html=True)






# #%%
# """
# Streamlit Web Interface for CFO AI Assistant
# """
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from src.orchestrator import CFOAssistant
# from src.config import Config

# # Page config
# st.set_page_config(
#     page_title="CFO AI Assistant",
#     page_icon="💼",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 1rem;
#     }
#     .sub-header {
#         font-size: 1.2rem;
#         color: #666;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .agent-badge {
#         display: inline-block;
#         padding: 0.25rem 0.75rem;
#         border-radius: 0.25rem;
#         font-size: 0.875rem;
#         font-weight: 600;
#         margin-bottom: 1rem;
#     }
#     .sql-badge {
#         background-color: #e3f2fd;
#         color: #1976d2;
#     }
#     .rag-badge {
#         background-color: #f3e5f5;
#         color: #7b1fa2;
#     }
#     .web-badge {
#         background-color: #e8f5e9;
#         color: #388e3c;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'assistant' not in st.session_state:
#     with st.spinner("Initializing CFO AI Assistant..."):
#         st.session_state.assistant = CFOAssistant()
#     st.success("✓ Assistant initialized!")

# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []

# # Sidebar
# with st.sidebar:
#     st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4bc.png", width=80)
#     st.title("CFO AI Assistant")
#     st.markdown("---")
    
#     st.subheader("🎯 Capabilities")
#     st.markdown("""
#     - 📊 **SQL Analysis**: Query financial data and metrics
#     - 📋 **Policy Search**: Find company policies and procedures
#     - 🌐 **Web Research**: Get current market insights
#     """)
    
#     st.markdown("---")
#     st.subheader("⚙️ Settings")
    
#     # Agent selection
#     agent_mode = st.radio(
#         "Agent Mode",
#         ["Auto (Recommended)", "Force SQL", "Force RAG", "Force Web"],
#         help="Auto mode automatically routes queries to the best agent"
#     )
    
#     # Clear chat button
#     if st.button("🗑️ Clear Chat History"):
#         st.session_state.chat_history = []
#         st.rerun()
    
#     st.markdown("---")
#     st.subheader("💡 Example Queries")
    
#     example_queries = {
#         "SQL": [
#             "Show top 5 companies by revenue",
#             "Compare tech vs healthcare profit margins",
#             "Which companies have ROE above 20%?"
#         ],
#         "RAG": [
#             "What's the expense approval policy?",
#             "How do we recognize subscription revenue?",
#             "What are our investment restrictions?"
#         ],
#         "Web": [
#             "Latest CFO trends in 2024",
#             "Current inflation impact on finance",
#             "Recent GAAP changes"
#         ]
#     }
    
#     for category, queries in example_queries.items():
#         with st.expander(f"{category} Examples"):
#             for query in queries:
#                 if st.button(query, key=f"example_{query}"):
#                     st.session_state.current_query = query

# # Main content
# st.markdown('<div class="main-header">💼 CFO AI Assistant</div>', unsafe_allow_html=True)
# st.markdown('<div class="sub-header">Your intelligent financial co-pilot for data, policies, and insights</div>', unsafe_allow_html=True)

# # Query input
# col1, col2 = st.columns([5, 1])
# with col1:
#     query = st.text_input(
#         "Ask me anything about financial data, company policies, or market insights:",
#         value=st.session_state.get('current_query', ''),
#         placeholder="e.g., Show me companies with profit margin above 15%",
#         key="query_input"
#     )
# with col2:
#     submit = st.button("🚀 Ask", type="primary", use_container_width=True)

# # Process query
# if submit and query:
#     # Clear the example query
#     if 'current_query' in st.session_state:
#         del st.session_state.current_query
    
#     # Determine force agent
#     force_agent = None
#     if agent_mode == "Force SQL":
#         force_agent = "sql"
#     elif agent_mode == "Force RAG":
#         force_agent = "rag"
#     elif agent_mode == "Force Web":
#         force_agent = "web"
    
#     # Process query
#     with st.spinner("🤔 Processing your query..."):
#         result = st.session_state.assistant.query(query, force_agent=force_agent)
    
#     # Add to history
#     st.session_state.chat_history.append({
#         "query": query,
#         "result": result
#     })

# # Display chat history
# if st.session_state.chat_history:
#     st.markdown("---")
    
#     for i, chat in enumerate(reversed(st.session_state.chat_history)):
#         with st.container():
#             # Query
#             st.markdown(f"### 💬 You asked:")
#             st.info(chat['query'])
            
#             # Response
#             result = chat['result']
            
#             # Agent badge
#             agent_class = ""
#             if "SQL" in result['agent_used']:
#                 agent_class = "sql-badge"
#             elif "RAG" in result['agent_used']:
#                 agent_class = "rag-badge"
#             elif "Web" in result['agent_used']:
#                 agent_class = "web-badge"
            
#             st.markdown(f'<span class="agent-badge {agent_class}">🤖 {result["agent_used"]}</span>', 
#                        unsafe_allow_html=True)
            
#             # Answer
#             st.markdown(result['answer'])
            
#             # Additional metadata
#             metadata = result.get('metadata', {})
            
#             # SQL-specific display
#             if metadata.get('sql_query'):
#                 with st.expander("🔍 View SQL Query"):
#                     st.code(metadata['sql_query'], language='sql')
                
#                 # Show dataframe if available
#                 if metadata.get('dataframe') is not None:
#                     df = metadata['dataframe']
#                     if not df.empty:
#                         with st.expander("📊 View Data Table"):
#                             st.dataframe(df, use_container_width=True)
                        
#                         # Auto-visualization for numeric data
#                         numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
#                         if len(numeric_cols) > 0 and len(df) > 1:
#                             with st.expander("📈 Visualization"):
#                                 # Create appropriate chart
#                                 if len(df) <= 20:  # Bar chart for smaller datasets
#                                     if len(numeric_cols) == 1:
#                                         fig = px.bar(df, x=df.columns[0], y=numeric_cols[0])
#                                     else:
#                                         fig = px.bar(df, x=df.columns[0], y=numeric_cols)
#                                 else:  # Line chart for larger datasets
#                                     fig = px.line(df, x=df.columns[0], y=numeric_cols)
                                
#                                 st.plotly_chart(fig, use_container_width=True)
            
#             # RAG-specific display
#             if metadata.get('sources'):
#                 with st.expander("📚 Sources"):
#                     for source in metadata['sources']:
#                         st.markdown(f"- {source}")
            
#             # Web-specific display
#             if metadata.get('sources') and isinstance(metadata['sources'], list) and len(metadata['sources']) > 0:
#                 if isinstance(metadata['sources'][0], dict):  # Web sources
#                     with st.expander("🔗 Web Sources"):
#                         for source in metadata['sources']:
#                             st.markdown(f"- [{source.get('title', 'Source')}]({source.get('url', '#')})")
            
#             # Error display
#             if result.get('error'):
#                 st.error(f"⚠️ Error: {result['error']}")
            
#             st.markdown("---")

# else:
#     # Welcome message
#     st.markdown("""
#     ### 👋 Welcome to CFO AI Assistant!
    
#     I can help you with:
    
#     1. **📊 Financial Analysis** - Query company data, metrics, and performance
#     2. **📋 Policy Information** - Search through company policies and procedures  
#     3. **🌐 Market Research** - Get current trends and external insights
    
#     **Try asking:**
#     - "Show me the top 10 companies by market cap"
#     - "What's our expense approval process?"
#     - "Latest trends in CFO priorities"
    
#     Select an example from the sidebar or type your own question above! 👆
#     """)

# # Footer
# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; color: #666; font-size: 0.875rem;">
#     Built with ❤️ using Claude (Anthropic), LangChain, ChromaDB, and Streamlit
# </div>
# """, unsafe_allow_html=True)
