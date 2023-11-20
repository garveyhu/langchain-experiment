from operator import itemgetter
from typing import List, Optional, Tuple

from langchain.schema import BaseMessage, format_document
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap, RunnablePassthrough
from langchain.vectorstores.elasticsearch import ElasticsearchStore
from pydantic import BaseModel, Field

from textcraft.models.embeddings.embedding_creator import get_embedding
from textcraft.models.llms.llm_creator import get_llm
from textcraft.prompts.esprompts import (
    CONDENSE_QUESTION_PROMPT,
    DOCUMENT_PROMPT,
    LLM_CONTEXT_PROMPT,
)
from textcraft.vectors.es.connection import get_es_connection

retriever = get_es_connection().as_retriever()


def _combine_documents(
    docs, document_prompt=DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


def _format_chat_history(chat_history: List[Tuple]) -> str:
    buffer = ""
    for dialogue_turn in chat_history:
        human = "Human: " + dialogue_turn[0]
        ai = "Assistant: " + dialogue_turn[1]
        buffer += "\n" + "\n".join([human, ai])
    return buffer


class ChainInput(BaseModel):
    chat_history: Optional[List[BaseMessage]] = Field(
        description="Previous chat messages."
    )
    question: str = Field(..., description="The question to answer.")


_inputs = RunnableMap(
    standalone_question=RunnablePassthrough.assign(
        chat_history=lambda x: _format_chat_history(x["chat_history"])
    )
    | CONDENSE_QUESTION_PROMPT
    | get_llm()
    | StrOutputParser(),
)

_context = {
    "context": itemgetter("standalone_question") | retriever | _combine_documents,
    "question": lambda x: x["standalone_question"],
}

chain = _inputs | _context | LLM_CONTEXT_PROMPT | get_llm() | StrOutputParser()

chain = chain.with_types(input_type=ChainInput)
