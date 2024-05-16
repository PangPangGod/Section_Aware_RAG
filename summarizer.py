import os
import pickle
import asyncio
from typing import Any, List
from string import Template

import numpy as np
from numpy import percentile, subtract, std
from sklearn.metrics.pairwise import cosine_similarity

# LangChain for Chat Models, Embeddings, and Output Parsing
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import pickle

from pydantic import BaseModel, Field
from typing import List, Optional

class TextElement(BaseModel):
    type: str
    text: str
    page_number: int
    table_index: Optional[int] = None
    is_table: bool = False


with open('elements_processed.pkl', 'rb') as file:
    elements = pickle.load(file)

print("List has been loaded.")

from typing import Dict, Literal

BREAKPOINTHRESHOLDTYPE = Literal["percentile", "standard_deviation", "interquartile"]
BREAKPOINT_DEFAULTS: Dict[BREAKPOINTHRESHOLDTYPE, float] = {
    "percentile": 95,
    "standard_deviation": 3,
    "interquartile": 1.5,
}


## summary chains here
class TableSummarizer:
    def __init__(self, embedding_model:Embeddings, elements):
        self.embedding_model = embedding_model
        self.model = "gpt-3.5-turbo-0125"
        self.elements = elements
        self.table_elements = []
        self.text_elements = []
    
    def _calculate_similarity_through_chunks(
            self, text_element, embedded_table: List[float], breakpoint_threshold_type: BREAKPOINTHRESHOLDTYPE = "percentile", breakpoint_threshold: float = None):
        """ Table Element 전체와 Text Element를 chunk 한 문장들과의 cosine 유사도를 구해서 threshold 이상이면 연관성이 존재한다고 판단,
        더해준 다음 SummaryAgent에 전달 후 MultiVectorRetriever에 이용. 추가적으로 통계적 분석을 통해 문장 필터링 가능."""

        # 옵션값 설정
        if breakpoint_threshold is None:
            breakpoint_threshold = BREAKPOINT_DEFAULTS[breakpoint_threshold_type]

        # 입력 텍스트 분리 및 임베딩
        splitted_text_chunk = text_element.text.split("\n")
        embedded_text_chunk = self.embedding_model.embed_documents(texts=[text for text in splitted_text_chunk])
        similarities = []
        result_context_to_insert = ""

        for embedded_text in embedded_text_chunk:
            similarity = cosine_similarity([embedded_text], embedded_table)[0][0]
            similarities.append(similarity)

        # 유사도 데이터를 array로 변환
        similarity_array = np.array(similarities)
        # 분석 기준값 계산
        if breakpoint_threshold_type == "percentile":
            breakpoint_value = percentile(similarity_array, breakpoint_threshold)
        elif breakpoint_threshold_type == "standard_deviation":
            mean_value = np.mean(similarity_array)
            breakpoint_value = mean_value + std(similarity_array) * breakpoint_threshold
        elif breakpoint_threshold_type == "interquartile":
            iqr = subtract(*percentile(similarity_array, [75, 25]))
            breakpoint_value = percentile(similarity_array, 75) + iqr * breakpoint_threshold

        # self.log_message(f"Threshold for filtering: {breakpoint_value}")

        # 유사도가 분석 기준값 이상인 문장만 결과에 추가
        for index, similarity in enumerate(similarities):
            if similarity > breakpoint_value:
                result_context_to_insert += splitted_text_chunk[index] + "\n"

        return result_context_to_insert

    def escape_braces(self, text):
        return text.replace('{', '{{').replace('}', '}}')

    async def _summarize_chain(self, context_key, context, element, model=ChatOpenAI, max_tokens=512, temperature=0):
        template = Template("You are an assistant tasked with summarizing html table with context.\n\
        Based on contexts below, please summarize the $context_key using the relevant context.\n\
        \n\
        Previous context: $prev_context $context_key: $element Following context: $after_context")

        prompt_text = template.substitute(context_key=context_key, prev_context=context['prev_context'], element=element, after_context=context['after_context'])
        prompt_text = self.escape_braces(prompt_text)
        prompt = ChatPromptTemplate.from_template(prompt_text)

        chain = (
            {context_key: lambda x: x, "prev_context": lambda x: context["prev_context"], "after_context": lambda x: context["after_context"]}
            | prompt
            | model(temperature=temperature, model=self.model, max_tokens=max_tokens)
            | StrOutputParser()
        )

        return await chain.ainvoke({context_key: element, "prev_context": context["prev_context"], "after_context": context["after_context"]})

    async def _summarize_table_chain(self, table_context, prev_context="", after_context=""):
        """ Wrapper function _summarize_chain """
        return await self._summarize_chain("table", {"prev_context": prev_context, "after_context": after_context}, table_context)

    async def _async_process_document(self):
        self.table_elements = [e.text for e in elements if e.type == "table"]
        self.text_elements = [e.text for e in elements if e.type == "text"]

        table_tasks = [
            self._summarize_table_chain(**self._get_context(element, elements), table_context=element.text)
            for element in elements if element.type == "table"
        ]

        table_summaries = await asyncio.gather(*table_tasks)
        return table_summaries

    def _get_context(self, element, elements):
        context = {"prev_context": "", "after_context": ""}
        index = elements.index(element)

        if index > 0 and elements[index-1].type == "text":
            prev_element = elements[index-1]
            prev_text = "".join([str(c) for c in prev_element.text])  # Extract text from Tag object
            context["prev_context"] = self._calculate_similarity_through_chunks(
                prev_element, self.embedding_model.embed_documents(texts=[prev_text])
            )

        if index < len(elements)-1 and elements[index+1].type == "text":
            next_element = elements[index+1]
            next_text = "".join([str(c) for c in next_element.text])  # Extract text from Tag object
            context["after_context"] = self._calculate_similarity_through_chunks(
                next_element, self.embedding_model.embed_documents(texts=[next_text])
            )

        return context
    
    async def execute(self):
        table_summaries = await self._async_process_document()

        print("="*80)
        # 결과 출력
        print("Table Summaries : ")
        for summary in table_summaries:
            print(summary)
        print("="*80, "Table summary, Text summary Execute with ainvoke complete.")

        return self.table_elements, table_summaries
    
from langchain_openai.embeddings import OpenAIEmbeddings
### Setup embeddings before setup retriever
embedding_model=OpenAIEmbeddings(model="text-embedding-3-small")
summarizer = TableSummarizer(
    embedding_model=embedding_model,
    elements=elements)


table_elements, table_summaries = asyncio.run(summarizer.execute())
### pkl 쓰지 말고 넘겨주는걸로.

print([str(element) for element in table_elements])

with open('table_summaries.pkl', 'wb') as f:
    pickle.dump(table_summaries, f)

print("Data has been saved to pickle files.")

