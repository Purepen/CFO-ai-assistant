"""
RAG Agent for Policy Documents with Conversation Memory
Handles document ingestion, retrieval, and Q&A
"""
import os
from pathlib import Path
from typing import List
from anthropic import Anthropic
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.config import Config


class RAGAgent:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=Config.VECTORSTORE_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"description": "Financial policy documents"}
        )
        
        # Initialize conversational chain with memory (created after documents are ingested)
        self.conversation_chain = None
        self.memory = None
    
    def _initialize_conversation_chain(self):
        """Initialize the conversational RAG chain with memory"""
        if self.conversation_chain is not None:
            return
        
        # Create LangChain-compatible embedding function
        embedding_function = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )
        
        # Create vector store
        vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=Config.COLLECTION_NAME,
            embedding_function=embedding_function
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # Create Claude LLM
        llm = ChatAnthropic(
            temperature=0,
            model=Config.ANTHROPIC_MODEL,
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            max_tokens=2048
        )
        
        # Set up conversation memory
        self.memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key='answer'
        )
        
        # Create conversational chain
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )
        
        print("✓ Conversation chain with memory initialized")
    
    def ingest_documents(self, force_reload: bool = False):
        """Load and index all policy documents"""
        
        # Check if already loaded
        if not force_reload and self.collection.count() > 0:
            print(f"Vector store already contains {self.collection.count()} chunks")
            return
        
        documents_dir = Path(Config.DOCUMENTS_DIR)
        
        if not documents_dir.exists():
            raise FileNotFoundError(f"Documents directory not found: {documents_dir}")
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        # Process each document
        for doc_path in documents_dir.glob("*.txt"):
            print(f"Processing {doc_path.name}...")
            
            with open(doc_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Split into chunks using LangChain
            chunks = self.text_splitter.split_text(text)
            
            # Create metadata and IDs for each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    "source": doc_path.name,
                    "chunk_id": i
                })
                all_ids.append(f"{doc_path.stem}_chunk_{i}")
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(all_chunks, show_progress_bar=True)
        
        # Add to ChromaDB
        print("Adding to vector store...")
        self.collection.add(
            documents=all_chunks,
            embeddings=embeddings.tolist(),
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        print(f"✓ Ingested {len(all_chunks)} chunks from {len(list(documents_dir.glob('*.txt')))} documents")
    
    def query(self, question: str, use_memory: bool = True) -> dict:
        """
        Answer question using RAG with optional conversation memory
        
        Args:
            question: User's question
            use_memory: If True, uses conversation memory for context
        
        Returns dict with: answer, sources, source_documents, error
        """
        try:
            # Initialize conversation chain if using memory
            if use_memory:
                if self.conversation_chain is None:
                    self._initialize_conversation_chain()
                
                # Use conversational chain with memory
                result = self.conversation_chain({"question": question})
                
                # Extract sources from documents
                sources = list(set([
                    doc.metadata.get('source', 'Unknown')
                    for doc in result.get('source_documents', [])
                ]))
                
                return {
                    "answer": result['answer'],
                    "sources": sources,
                    "source_documents": result.get('source_documents', []),
                    "error": None
                }
            
            # Fallback to stateless query (original implementation)
            else:
                return self._stateless_query(question)
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "sources": [],
                "source_documents": [],
                "error": str(e)
            }
    
    def _stateless_query(self, question: str) -> dict:
        """Original stateless query method (for backward compatibility)"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([question])[0]
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        if not results['documents'][0]:
            return {
                "answer": "I couldn't find any relevant information in the policy documents.",
                "sources": [],
                "source_documents": [],
                "error": None
            }
        
        # Build context
        context = "\n\n---\n\n".join([
            f"From {results['metadatas'][0][i]['source']}:\n{results['documents'][0][i]}"
            for i in range(len(results['documents'][0]))
        ])
        
        # Generate answer
        prompt = f"""You are a helpful financial policy assistant. Answer the user's question based on the provided policy documents.

Policy Documents Context:
{context}

User Question: {question}

Instructions:
1. Answer the question clearly and accurately based on the policy documents
2. Cite specific policy names and sections when relevant
3. If the documents don't contain the answer, say so
4. Be specific with numbers, thresholds, and requirements
5. Use a professional, CFO-appropriate tone

Answer:"""

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sources = list(set([results['metadatas'][0][i]['source'] for i in range(len(results['metadatas'][0]))]))
        
        return {
            "answer": response.content[0].text,
            "sources": sources,
            "source_documents": [],
            "error": None
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()
            print("✓ Conversation memory cleared")
    
    def get_conversation_history(self) -> list:
        """Get the conversation history"""
        if self.memory:
            return self.memory.chat_memory.messages
        return []


# # Setup and test function
# def setup_and_test():
#     print("Initializing RAG Agent...")
#     agent = RAGAgent()
    
#     print("\nIngesting documents...")
#     agent.ingest_documents(force_reload=False)
    
#     print("\n" + "="*60)
#     print("Testing RAG Agent WITH Memory")
#     print("="*60)
    
#     # Test conversation with memory
#     print("\n--- Conversation 1 ---")
#     result1 = agent.query("What's the approval threshold for expenses over $10,000?", use_memory=True)
#     print(f"Q: What's the approval threshold for expenses over $10,000?")
#     print(f"A: {result1['answer'][:200]}...")
    
#     print("\n--- Conversation 2 (Follow-up) ---")
#     result2 = agent.query("What about for capital expenditures?", use_memory=True)
#     print(f"Q: What about for capital expenditures?")
#     print(f"A: {result2['answer'][:200]}...")
    
#     print("\n--- Clear Memory ---")
#     agent.clear_memory()
    
#     print("\n--- Conversation 3 (After clear) ---")
#     result3 = agent.query("What about for capital expenditures?", use_memory=True)
#     print(f"Q: What about for capital expenditures? (no context)")
#     print(f"A: {result3['answer'][:200]}...")


# if __name__ == "__main__":
#     setup_and_test()







# """
# RAG Agent for Policy Documents
# Handles document ingestion, retrieval, and Q&A
# """
# import os
# from pathlib import Path
# from typing import List
# from anthropic import Anthropic
# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from src.config import Config


# class RAGAgent:
#     def __init__(self):
#         self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
#         self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
#         # Initialize LangChain text splitter
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200,
#             length_function=len,
#             separators=["\n\n", "\n", ". ", " ", ""]
#         )
        
#         # Initialize ChromaDB
#         self.chroma_client = chromadb.PersistentClient(
#             path=Config.VECTORSTORE_DIR,
#             settings=Settings(anonymized_telemetry=False)
#         )
        
#         # Get or create collection
#         self.collection = self.chroma_client.get_or_create_collection(
#             name=Config.COLLECTION_NAME,
#             metadata={"description": "Financial policy documents"}
#         )
    
#     def ingest_documents(self, force_reload: bool = False):
#         """Load and index all policy documents"""
        
#         # Check if already loaded
#         if not force_reload and self.collection.count() > 0:
#             print(f"Vector store already contains {self.collection.count()} chunks")
#             return
        
#         documents_dir = Path(Config.DOCUMENTS_DIR)
        
#         if not documents_dir.exists():
#             raise FileNotFoundError(f"Documents directory not found: {documents_dir}")
        
#         all_chunks = []
#         all_metadatas = []
#         all_ids = []
        
#         # Process each document
#         for doc_path in documents_dir.glob("*.txt"):
#             print(f"Processing {doc_path.name}...")
            
#             with open(doc_path, 'r', encoding='utf-8') as f:
#                 text = f.read()
            
#             # Split into chunks using LangChain
#             chunks = self.text_splitter.split_text(text)
            
#             # Create metadata and IDs for each chunk
#             for i, chunk in enumerate(chunks):
#                 all_chunks.append(chunk)
#                 all_metadatas.append({
#                     "source": doc_path.name,
#                     "chunk_id": i
#                 })
#                 all_ids.append(f"{doc_path.stem}_chunk_{i}")
        
#         # Generate embeddings
#         print("Generating embeddings...")
#         embeddings = self.embedding_model.encode(all_chunks, show_progress_bar=True)
        
#         # Add to ChromaDB
#         print("Adding to vector store...")
#         self.collection.add(
#             documents=all_chunks,
#             embeddings=embeddings.tolist(),
#             metadatas=all_metadatas,
#             ids=all_ids
#         )
        
#         print(f"✓ Ingested {len(all_chunks)} chunks from {len(list(documents_dir.glob('*.txt')))} documents")
    
#     def _retrieve_relevant_chunks(self, query: str, n_results: int = 5) -> List[dict]:
#         """Retrieve most relevant document chunks"""
        
#         # Generate query embedding
#         query_embedding = self.embedding_model.encode([query])[0]
        
#         # Query ChromaDB
#         results = self.collection.query(
#             query_embeddings=[query_embedding.tolist()],
#             n_results=n_results
#         )
        
#         # Format results
#         chunks = []
#         for i in range(len(results['documents'][0])):
#             chunks.append({
#                 'content': results['documents'][0][i],
#                 'source': results['metadatas'][0][i]['source'],
#                 'distance': results['distances'][0][i] if 'distances' in results else None
#             })
        
#         return chunks
    
#     def query(self, question: str) -> dict:
#         """
#         Answer question using RAG
#         Returns dict with: answer, sources, chunks, error
#         """
#         try:
#             # Retrieve relevant chunks
#             relevant_chunks = self._retrieve_relevant_chunks(question)
            
#             if not relevant_chunks:
#                 return {
#                     "answer": "I couldn't find any relevant information in the policy documents.",
#                     "sources": [],
#                     "chunks": [],
#                     "error": None
#                 }
            
#             # Build context from chunks
#             context = "\n\n---\n\n".join([
#                 f"From {chunk['source']}:\n{chunk['content']}"
#                 for chunk in relevant_chunks
#             ])
            
#             # Generate answer with Claude
#             prompt = f"""You are a helpful financial policy assistant. Answer the user's question based on the provided policy documents.

# Policy Documents Context:
# {context}

# User Question: {question}

# Instructions:
# 1. Answer the question clearly and accurately based on the policy documents
# 2. Cite specific policy names and sections when relevant
# 3. If the documents don't contain the answer, say so
# 4. Be specific with numbers, thresholds, and requirements
# 5. Use a professional, CFO-appropriate tone

# Answer:"""

#             response = self.client.messages.create(
#                 model=Config.ANTHROPIC_MODEL,
#                 max_tokens=2048,
#                 temperature=0,
#                 messages=[{"role": "user", "content": prompt}]
#             )
            
#             answer = response.content[0].text
            
#             # Extract unique sources
#             sources = list(set([chunk['source'] for chunk in relevant_chunks]))
            
#             return {
#                 "answer": answer,
#                 "sources": sources,
#                 "chunks": relevant_chunks,
#                 "error": None
#             }
            
#         except Exception as e:
#             return {
#                 "answer": f"I encountered an error: {str(e)}",
#                 "sources": [],
#                 "chunks": [],
#                 "error": str(e)
#             }


# # Setup and test function
# def setup_and_test():
#     print("Initializing RAG Agent...")
#     agent = RAGAgent()
    
#     print("\nIngesting documents...")
#     agent.ingest_documents(force_reload=False)
    
#     print("\n" + "="*60)
#     print("Testing RAG Agent")
#     print("="*60)
    
#     test_questions = [
#         "What's the approval threshold for expenses over $10,000?",
#         "How should we recognize revenue from multi-year contracts?",
#         "What are the requirements for international travel expenses?",
#         "What investments are prohibited according to our policy?"
#     ]
    
#     for question in test_questions:
#         print(f"\n{'='*60}")
#         print(f"Q: {question}")
#         print('='*60)
#         result = agent.query(question)
#         print(f"Sources: {', '.join(result['sources'])}")
#         print(f"\nAnswer:\n{result['answer']}")


# if __name__ == "__main__":
#     setup_and_test()






















# #%%
# """
# RAG Agent for Policy Documents
# Handles document ingestion, retrieval, and Q&A
# """

# import os
# from pathlib import Path
# from typing import List
# from anthropic import Anthropic
# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer
# from src.config import Config


# class RAGAgent:
#     def __init__(self):
#         self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
#         self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
#         # Initialize ChromaDB
#         self.chroma_client = chromadb.PersistentClient(
#             path=Config.VECTORSTORE_DIR,
#             settings=Settings(anonymized_telemetry=False)
#         )
        
#         # Get or create collection
#         self.collection = self.chroma_client.get_or_create_collection(
#             name=Config.COLLECTION_NAME,
#             metadata={"description": "Financial policy documents"}
#         )
        
#     def _chunk_document(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
#         """Split document into overlapping chunks"""
#         chunks = []
#         start = 0
#         text_length = len(text)
        
#         while start < text_length:
#             end = start + chunk_size
#             chunk = text[start:end]
            
#             # Try to break at sentence boundary
#             if end < text_length:
#                 last_period = chunk.rfind('.')
#                 if last_period > chunk_size * 0.5:  # Only if we're past halfway
#                     end = start + last_period + 1
#                     chunk = text[start:end]
            
#             chunks.append(chunk.strip())
#             start = end - overlap
        
#         return chunks
    
#     def ingest_documents(self, force_reload: bool = False):
#         """Load and index all policy documents"""
        
#         # Check if already loaded
#         if not force_reload and self.collection.count() > 0:
#             print(f"Vector store already contains {self.collection.count()} chunks")
#             return
        
#         documents_dir = Path(Config.DOCUMENTS_DIR)
        
#         if not documents_dir.exists():
#             raise FileNotFoundError(f"Documents directory not found: {documents_dir}")
        
#         all_chunks = []
#         all_metadatas = []
#         all_ids = []
        
#         # Process each document
#         for doc_path in documents_dir.glob("*.txt"):
#             print(f"Processing {doc_path.name}...")
            
#             with open(doc_path, 'r', encoding='utf-8') as f:
#                 text = f.read()
            
#             # Split into chunks
#             chunks = self._chunk_document(text)
            
#             # Create metadata and IDs for each chunk
#             for i, chunk in enumerate(chunks):
#                 all_chunks.append(chunk)
#                 all_metadatas.append({
#                     "source": doc_path.name,
#                     "chunk_id": i
#                 })
#                 all_ids.append(f"{doc_path.stem}_chunk_{i}")
        
#         # Generate embeddings
#         print("Generating embeddings...")
#         embeddings = self.embedding_model.encode(all_chunks, show_progress_bar=True)
        
#         # Add to ChromaDB
#         print("Adding to vector store...")
#         self.collection.add(
#             documents=all_chunks,
#             embeddings=embeddings.tolist(),
#             metadatas=all_metadatas,
#             ids=all_ids
#         )
        
#         print(f"✓ Ingested {len(all_chunks)} chunks from {len(list(documents_dir.glob('*.txt')))} documents")
    
#     def _retrieve_relevant_chunks(self, query: str, n_results: int = 5) -> List[dict]:
#         """Retrieve most relevant document chunks"""
        
#         # Generate query embedding
#         query_embedding = self.embedding_model.encode([query])[0]
        
#         # Query ChromaDB
#         results = self.collection.query(
#             query_embeddings=[query_embedding.tolist()],
#             n_results=n_results
#         )
        
#         # Format results
#         chunks = []
#         for i in range(len(results['documents'][0])):
#             chunks.append({
#                 'content': results['documents'][0][i],
#                 'source': results['metadatas'][0][i]['source'],
#                 'distance': results['distances'][0][i] if 'distances' in results else None
#             })
        
#         return chunks
    
#     def query(self, question: str) -> dict:
#         """
#         Answer question using RAG
#         Returns dict with: answer, sources, chunks, error
#         """
#         try:
#             # Retrieve relevant chunks
#             relevant_chunks = self._retrieve_relevant_chunks(question)
            
#             if not relevant_chunks:
#                 return {
#                     "answer": "I couldn't find any relevant information in the policy documents.",
#                     "sources": [],
#                     "chunks": [],
#                     "error": None
#                 }
            
#             # Build context from chunks
#             context = "\n\n---\n\n".join([
#                 f"From {chunk['source']}:\n{chunk['content']}"
#                 for chunk in relevant_chunks
#             ])
            
#             # Generate answer with Claude
#             prompt = f"""You are a helpful financial policy assistant. Answer the user's question based on the provided policy documents.

# Policy Documents Context:
# {context}

# User Question: {question}

# Instructions:
# 1. Answer the question clearly and accurately based on the policy documents
# 2. Cite specific policy names and sections when relevant
# 3. If the documents don't contain the answer, say so
# 4. Be specific with numbers, thresholds, and requirements
# 5. Use a professional, CFO-appropriate tone

# Answer:"""

#             response = self.client.messages.create(
#                 model=Config.ANTHROPIC_MODEL,
#                 max_tokens=2048,
#                 temperature=0,
#                 messages=[{"role": "user", "content": prompt}]
#             )
            
#             answer = response.content[0].text
            
#             # Extract unique sources
#             sources = list(set([chunk['source'] for chunk in relevant_chunks]))
            
#             return {
#                 "answer": answer,
#                 "sources": sources,
#                 "chunks": relevant_chunks,
#                 "error": None
#             }
            
#         except Exception as e:
#             return {
#                 "answer": f"I encountered an error: {str(e)}",
#                 "sources": [],
#                 "chunks": [],
#                 "error": str(e)
#             }


# # Setup and test function
# def setup_and_test():
#     print("Initializing RAG Agent...")
#     agent = RAGAgent()
    
#     print("\nIngesting documents...")
#     agent.ingest_documents(force_reload=False)
    
#     print("\n" + "="*60)
#     print("Testing RAG Agent")
#     print("="*60)
    
#     test_questions = [
#         "What's the approval threshold for expenses over $10,000?",
#         "How should we recognize revenue from multi-year contracts?",
#         "What are the requirements for international travel expenses?",
#         "What investments are prohibited according to our policy?"
#     ]
    
#     for question in test_questions:
#         print(f"\n{'='*60}")
#         print(f"Q: {question}")
#         print('='*60)
#         result = agent.query(question)
#         print(f"Sources: {', '.join(result['sources'])}")
#         print(f"\nAnswer:\n{result['answer']}")


# if __name__ == "__main__":
#     setup_and_test()

# # %%
