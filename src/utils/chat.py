from src.utils.helpers import (
    HuggingFaceInferenceAPIEmbeddings,
    MongoDBChatMessageHistory,
    LangChainMongoDBVectorSearch,
    ChatGroq,
    ChatPromptTemplate,
    MessagesPlaceholder,
    RunnablePassthrough,
    RunnableWithMessageHistory,
    StrOutputParser,
    Customexception
)
from src.utils.prompt import Chat_promt, chat_rag_prompt
from functools import lru_cache       
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os, sys

load_dotenv()
MONGO_URI = os.environ.get("MONGO_URI")
HF_KEY = os.environ.get("HF_KEY")

class ChatSettings:
    MONGO_URI: str = MONGO_URI
    HF_KEY: str = HF_KEY
    DB_NAME: str = "Financial_statement"
    COLLECTION_NAME: str = "fin_document"
    CHAT_HISTORY_COLLECTION: str = "chat_histories"

settings = ChatSettings()

@lru_cache()
def get_embeddings():
    return HuggingFaceInferenceAPIEmbeddings(
        api_key=settings.HF_KEY,
        model_name="BAAI/bge-small-en-v1.5"
    )

@lru_cache()
def get_vector_store():
    embeddings = get_embeddings()
    return LangChainMongoDBVectorSearch.from_connection_string(
        connection_string = settings.MONGO_URI,
        namespace = f"{settings.DB_NAME}.{settings.COLLECTION_NAME}",
        embedding = embeddings,
        index_name = "vector_index"
    )


class Chat:
    def __init__(self, model: str, temperature: float ):
        self.llm = ChatGroq(
            model = model,
            temperature=temperature,
            max_tokens=1024
        )
        self.vector_store = get_vector_store()
        self.retriever = self.vector_store.as_retriever(
            search_type = "similarity",
            search_kwargs = {"k": 5}
        )
        self.parse_output = StrOutputParser()
    
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        prompt = Chat_promt()
        question_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        
        return RunnablePassthrough.assign(
            context=question_prompt | self.llm | self.parse_output | self.retriever | 
            (lambda docs: "\n\n".join([d.page_content for d in docs]))
        )

    def get_rag_template(self) -> ChatPromptTemplate:
        prompt_rag = chat_rag_prompt()
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_rag),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        
        retrieval_chain = self.get_prompt_template()
        return retrieval_chain | rag_prompt | self.llm | self.parse_output
    
    def get_message_history(self, session_id : str):
        return MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=settings.MONGO_URI,
            database_name=settings.DB_NAME,
            collection_name=settings.CHAT_HISTORY_COLLECTION
        )
    
    async def generate_response(self, question : str, session_id : str):
        try:
            chat_llm = RunnableWithMessageHistory(
                self.get_rag_template(),
                self.get_message_history,
                input_messages_key="question",
                history_messages_key="history"
            )

            config = {"configurable": {"session_id": session_id}}
            response = await chat_llm.ainvoke(
                {"question": question},
                config=config
            )

            
            return response
        except Exception as e:
            raise Customexception(e, sys)
