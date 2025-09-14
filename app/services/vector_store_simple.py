"""
Simple Vector Store Implementation using FAISS
Fallback for ChromaDB when dependencies are missing
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

    # Fallback dummy classes
    class Document:
        def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class RecursiveCharacterTextSplitter:
        def __init__(self, **kwargs):
            pass

        def split_text(self, text: str) -> List[str]:
            return [text]


from dotenv import load_dotenv

load_dotenv()


class SimpleVectorStoreService:
    """
    Simple FAISS-based vector store as ChromaDB alternative
    """

    def __init__(self):
        """Initialize simple vector store"""
        self.persist_directory = os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./data/vectordb_simple"
        )
        self.collection_name = os.getenv(
            "CHROMA_COLLECTION_NAME", "kakao_alimtalk_policies"
        )

        # Create persist directory
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        if not FAISS_AVAILABLE:
            print("WARNING: FAISS not available. Vector search will be disabled.")
            self.vector_store = None
            self.embeddings = None
            return

        # OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-small",
        )

        # Vector store
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize FAISS vector store"""
        if not FAISS_AVAILABLE:
            return

        try:
            faiss_index_path = Path(self.persist_directory) / "index.faiss"
            faiss_pkl_path = Path(self.persist_directory) / "index.pkl"

            if faiss_index_path.exists() and faiss_pkl_path.exists():
                # Load existing index
                self.vector_store = FAISS.load_local(
                    self.persist_directory,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print(
                    f"Existing FAISS vector store loaded from {self.persist_directory}"
                )
            else:
                # Create empty vector store
                print("Creating new empty FAISS vector store")

        except Exception as e:
            print(f"Vector store initialization error: {e}")

    def load_and_embed_policies(
        self, policies_dir: str = "./data/cleaned_policies"
    ) -> bool:
        """
        Load and embed policy documents
        """
        if not FAISS_AVAILABLE:
            print("FAISS not available - skipping policy embedding")
            return False

        try:
            policies_path = Path(policies_dir)
            if not policies_path.exists():
                print(f"Policy directory not found: {policies_dir}")
                # Create dummy data for testing
                return self._create_dummy_policies()

            # Find markdown files
            md_files = list(policies_path.glob("*.md"))
            if not md_files:
                print(f"No policy documents found in: {policies_dir}")
                return self._create_dummy_policies()

            print(f"Loading {len(md_files)} policy documents...")

            # Load and chunk documents
            documents = []
            for md_file in md_files:
                print(f"  - Processing {md_file.name}...")
                content = self._load_markdown_file(md_file)
                if content:
                    doc_chunks = self._split_document(content, md_file.stem)
                    documents.extend(doc_chunks)

            if not documents:
                print("No documents to embed.")
                return self._create_dummy_policies()

            print(f"Embedding {len(documents)} document chunks...")

            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
            else:
                self.vector_store.add_documents(documents)

            # Save vector store
            self.vector_store.save_local(self.persist_directory)

            print("Policy document embedding completed!")
            return True

        except Exception as e:
            print(f"Policy document embedding error: {e}")
            return self._create_dummy_policies()

    def _create_dummy_policies(self) -> bool:
        """Create dummy policy data for testing"""
        if not FAISS_AVAILABLE:
            return False

        try:
            # Create some dummy policy documents
            dummy_policies = [
                {
                    "content": "카카오톡 알림톡은 카카오톡을 통해 전송되는 정보성 메시지입니다. 광고성 내용은 포함할 수 없습니다.",
                    "source": "alimtalk_basic_rules",
                },
                {
                    "content": "템플릿에는 변수를 사용할 수 있으며, #{변수명} 형태로 작성합니다. 한 템플릿당 최대 10개까지 변수 사용 가능합니다.",
                    "source": "template_variable_rules",
                },
                {
                    "content": "할인, 이벤트, 프로모션과 관련된 내용은 광고성 메시지로 분류되어 알림톡에서 사용할 수 없습니다.",
                    "source": "advertising_content_restrictions",
                },
                {
                    "content": "주문 확인, 배송 안내, 예약 확인과 같은 거래 관련 정보는 알림톡으로 전송 가능합니다.",
                    "source": "transactional_message_guidelines",
                },
                {
                    "content": "템플릿 승인 시 카카오의 정책을 준수해야 하며, 부적절한 내용이 포함된 경우 반려될 수 있습니다.",
                    "source": "template_approval_process",
                },
            ]

            # Convert to Document objects
            documents = []
            for i, policy in enumerate(dummy_policies):
                doc = Document(
                    page_content=policy["content"],
                    metadata={
                        "source": policy["source"],
                        "chunk_id": 0,
                        "total_chunks": 1,
                        "document_type": "policy",
                        "language": "korean",
                    },
                )
                documents.append(doc)

            # Create vector store
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            self.vector_store.save_local(self.persist_directory)

            print("Dummy policy data created for testing!")
            return True

        except Exception as e:
            print(f"Error creating dummy policies: {e}")
            return False

    def _load_markdown_file(self, file_path: Path) -> Optional[str]:
        """Load markdown file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"File load error ({file_path}): {e}")
            return None

    def _split_document(self, content: str, source: str) -> List[Document]:
        """Split document into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

        chunks = text_splitter.split_text(content)

        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": source,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "document_type": "policy",
                    "language": "korean",
                },
            )
            documents.append(doc)

        return documents

    def similarity_search(
        self, query: str, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Similarity search"""
        if not FAISS_AVAILABLE or not self.vector_store:
            print("Vector search not available")
            return []

        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Document search error: {e}")
            return []

    def similarity_search_with_score(
        self, query: str, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Similarity search with scores"""
        if not FAISS_AVAILABLE or not self.vector_store:
            print("Vector search not available")
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"Document search with score error: {e}")
            return []

    def get_relevant_policies(
        self, user_query: str, template_type: Optional[str] = None, k: int = 5
    ) -> Dict[str, Any]:
        """Get relevant policy information"""
        try:
            results = self.similarity_search_with_score(user_query, k=k)

            policies = []
            for doc, score in results:
                policy_info = {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "relevance_score": float(score),
                    "metadata": doc.metadata,
                }
                policies.append(policy_info)

            return {
                "query": user_query,
                "total_results": len(policies),
                "policies": policies,
            }

        except Exception as e:
            print(f"Relevant policy search error: {e}")
            return {"query": user_query, "total_results": 0, "policies": []}

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        if not FAISS_AVAILABLE or not self.vector_store:
            return {
                "name": self.collection_name,
                "count": 0,
                "metadata": {"status": "not_available"},
            }

        try:
            # FAISS doesn't have a direct count method, so we estimate
            return {
                "name": self.collection_name,
                "count": (
                    self.vector_store.index.ntotal
                    if hasattr(self.vector_store, "index")
                    else 0
                ),
                "metadata": {"status": "available", "type": "faiss"},
            }
        except Exception as e:
            print(f"Collection info error: {e}")
            return {
                "name": self.collection_name,
                "count": 0,
                "metadata": {"status": "error"},
            }


# Global instance
simple_vector_store_service = SimpleVectorStoreService()
