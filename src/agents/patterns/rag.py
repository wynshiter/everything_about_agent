"""
Retrieval-Augmented Generation (RAG) Pattern Implementation
Chapter 14: RAG

检索增强生成模式 - 结合外部知识库检索与 LLM 生成能力，
提供更准确、有依据的回答。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@dataclass
class Document:
    """文档定义"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.id:
            # 根据内容生成 ID
            self.id = hashlib.md5(self.content.encode()).hexdigest()[:12]


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    rank: int


class SimpleVectorStore:
    """
    简单向量存储实现
    用于演示 RAG 核心概念（生产环境应使用专用向量数据库）
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.documents: Dict[str, Document] = {}
        self._initialized = False
        logger.info(f"Vector store '{name}' initialized")
    
    def add_document(self, doc: Document) -> str:
        """添加文档"""
        self.documents[doc.id] = doc
        logger.debug(f"Added document: {doc.id}")
        return doc.id
    
    def add_documents(self, docs: List[Document]) -> List[str]:
        """批量添加文档"""
        return [self.add_document(d) for d in docs]
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        简单的关键词搜索（演示用）
        实际实现应使用向量相似度搜索
        """
        query_terms = query.lower().split()
        scored_docs = []
        
        for doc in self.documents.values():
            # 简单的 TF 分数计算
            score = sum(1 for term in query_terms if term in doc.content.lower())
            if score > 0:
                scored_docs.append((doc, score))
        
        # 按分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 k 个
        results = []
        for i, (doc, score) in enumerate(scored_docs[:top_k], 1):
            results.append(SearchResult(document=doc, score=score, rank=i))
        
        return results
    
    def count(self) -> int:
        """文档数量"""
        return len(self.documents)


class Retriever:
    """
    检索器
    负责从向量存储中检索相关文档
    """
    
    def __init__(self, vector_store: SimpleVectorStore, top_k: int = 5):
        self.vector_store = vector_store
        self.top_k = top_k
    
    def retrieve(self, query: str, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """
        检索相关文档
        
        Args:
            query: 查询字符串
            filters: 元数据过滤器
        
        Returns:
            搜索结果列表
        """
        results = self.vector_store.search(query, self.top_k)
        
        # 应用过滤器
        if filters:
            filtered = []
            for result in results:
                doc_metadata = result.document.metadata
                match = all(
                    doc_metadata.get(k) == v for k, v in filters.items()
                )
                if match:
                    filtered.append(result)
            results = filtered
        
        logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
        return results
    
    def get_context_string(self, query: str, max_length: int = 2000) -> str:
        """
        获取格式化的上下文字符串
        
        Args:
            query: 查询字符串
            max_length: 最大长度
        
        Returns:
            格式化的上下文
        """
        results = self.retrieve(query)
        
        if not results:
            return ""
        
        contexts = []
        current_length = 0
        
        for result in results:
            doc = result.document
            context_text = f"[{doc.metadata.get('source', 'Unknown')}]\n{doc.content}\n"
            
            if current_length + len(context_text) > max_length:
                break
            
            contexts.append(context_text)
            current_length += len(context_text)
        
        return "\n---\n".join(contexts)


class RAGAgent:
    """
    RAG Agent 实现
    结合检索和生成能力
    """
    
    def __init__(self, model_id: str = None, 
                 vector_store: Optional[SimpleVectorStore] = None,
                 top_k: int = 5):
        self.llm = model_loader.load_llm(model_id)
        self.vector_store = vector_store or SimpleVectorStore()
        self.retriever = Retriever(self.vector_store, top_k=top_k)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"📚 RAGAgent initialized with model: {effective_id}")
    
    def ingest_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        摄入文档到知识库
        
        Args:
            content: 文档内容
            metadata: 文档元数据
        
        Returns:
            文档 ID
        """
        doc = Document(
            content=content,
            metadata=metadata or {}
        )
        return self.vector_store.add_document(doc)
    
    def ingest_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """批量摄入文档"""
        docs = [
            Document(content=d["content"], metadata=d.get("metadata", {}))
            for d in documents
        ]
        return self.vector_store.add_documents(docs)
    
    def query(self, question: str, include_sources: bool = True) -> Dict[str, Any]:
        """
        查询知识库并生成回答
        
        Args:
            question: 用户问题
            include_sources: 是否包含来源信息
        
        Returns:
            包含回答和元数据的字典
        """
        # 1. 检索相关文档
        context = self.retriever.get_context_string(question)
        
        if not context:
            logger.warning("No relevant documents found")
            return {
                "answer": "未找到相关信息。",
                "sources": [],
                "context_used": False
            }
        
        # 2. 构建 RAG 提示
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个基于检索的问答助手。使用以下检索到的上下文来回答问题。
如果上下文中没有足够信息，请明确说明。
始终保持回答的准确性和相关性。"""),
            ("user", """上下文信息:
{context}

基于以上上下文，回答问题: {question}

要求:
1. 只使用上下文中的信息
2. 如果信息不足，直接说明
3. 引用来源时标注 [source:X]""")
        ])
        
        # 3. 生成回答
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        # 4. 获取来源
        sources = []
        if include_sources:
            results = self.retriever.retrieve(question)
            sources = [
                {
                    "id": r.document.id,
                    "source": r.document.metadata.get("source", "Unknown"),
                    "score": r.score,
                    "preview": r.document.content[:200] + "..."
                }
                for r in results[:3]
            ]
        
        logger.info(f"RAG query answered using {len(sources)} sources")
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": True
        }
    
    def add_to_knowledge_base(self, texts: List[str], 
                             source: str = "user_upload",
                             chunk_size: int = 500) -> List[str]:
        """
        添加文本到知识库（自动分块）
        
        Args:
            texts: 文本列表
            source: 来源标识
            chunk_size: 分块大小
        
        Returns:
            添加的文档 ID 列表
        """
        doc_ids = []
        
        for text in texts:
            # 简单分块（实际应使用更智能的分块策略）
            chunks = self._simple_chunk(text, chunk_size)
            
            for i, chunk in enumerate(chunks):
                doc_id = self.ingest_document(
                    content=chunk,
                    metadata={
                        "source": source,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                doc_ids.append(doc_id)
        
        logger.info(f"Added {len(doc_ids)} chunks to knowledge base")
        return doc_ids
    
    def _simple_chunk(self, text: str, chunk_size: int) -> List[str]:
        """简单文本分块"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计"""
        return {
            "total_documents": self.vector_store.count(),
            "vector_store_name": self.vector_store.name,
            "retriever_top_k": self.retriever.top_k
        }


class AdvancedRAGAgent(RAGAgent):
    """
    高级 RAG Agent
    支持查询重写、多轮检索等高级功能
    """
    
    def rewrite_query(self, original_query: str, conversation_history: List[str] = None) -> str:
        """
        重写查询以提高检索质量
        
        Args:
            original_query: 原始查询
            conversation_history: 对话历史
        
        Returns:
            优化后的查询
        """
        history_context = ""
        if conversation_history:
            history_context = "相关历史:\n" + "\n".join(conversation_history[-3:])
        
        prompt = ChatPromptTemplate.from_template("""
优化以下查询以提高检索效果:

原始查询: {query}
{history}

请生成一个更清晰、更具体的查询版本，包含关键概念和同义词。
只输出优化后的查询，不要解释。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        rewritten = chain.invoke({
            "query": original_query,
            "history": history_context
        })
        
        logger.info(f"Query rewritten: '{original_query}' -> '{rewritten[:100]}...'")
        return rewritten.strip()
    
    def multi_step_retrieve(self, query: str, num_iterations: int = 2) -> List[SearchResult]:
        """
        多步检索
        通过迭代改进检索结果
        """
        all_results = []
        current_query = query
        
        for i in range(num_iterations):
            results = self.retriever.retrieve(current_query)
            all_results.extend(results)
            
            # 基于结果生成新的查询
            if i < num_iterations - 1 and results:
                context = "\n".join([r.document.content[:200] for r in results[:2]])
                current_query = self._generate_follow_up_query(query, context)
        
        # 去重并重新排序
        seen_ids = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.document.id not in seen_ids:
                seen_ids.add(r.document.id)
                unique_results.append(r)
        
        return unique_results[:self.retriever.top_k]
    
    def _generate_follow_up_query(self, original: str, context: str) -> str:
        """生成跟进查询"""
        prompt = ChatPromptTemplate.from_template("""
基于以下信息，生成一个补充查询以获取更多相关信息:

原始查询: {original}
已获信息: {context}

生成一个补充查询:
""")
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"original": original, "context": context[:500]}).strip()


if __name__ == "__main__":
    print("=" * 60)
    print("RAG (Retrieval-Augmented Generation) Pattern Demo")
    print("=" * 60)
    
    # 创建 RAG Agent
    agent = RAGAgent()
    
    # 添加示例文档到知识库
    documents = [
        {
            "content": "Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。",
            "metadata": {"source": "python_intro", "topic": "programming"}
        },
        {
            "content": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习。",
            "metadata": {"source": "ml_basics", "topic": "ai"}
        },
        {
            "content": "深度学习是机器学习的一种，使用多层神经网络来模拟人脑的工作方式。",
            "metadata": {"source": "deep_learning", "topic": "ai"}
        },
        {
            "content": "Transformer 是一种深度学习架构，广泛应用于自然语言处理任务。",
            "metadata": {"source": "transformer", "topic": "nlp"}
        }
    ]
    
    doc_ids = agent.ingest_documents(documents)
    print(f"\n--- Added {len(doc_ids)} documents to knowledge base ---")
    
    # 显示统计
    stats = agent.get_knowledge_base_stats()
    print(f"Total documents: {stats['total_documents']}")
    
    # 演示查询
    print("\n--- Sample Queries ---")
    test_queries = [
        "什么是 Python？",
        "机器学习和深度学习有什么关系？",
        "Transformer 是什么？"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        # 检索结果
        results = agent.retriever.retrieve(query)
        print(f"Retrieved {len(results)} documents")
        for r in results[:2]:
            print(f"  - [{r.document.metadata.get('source', 'Unknown')}] score={r.score:.2f}")
    
    print("\n--- Note ---")
    print("Full RAG query requires LLM backend running")
