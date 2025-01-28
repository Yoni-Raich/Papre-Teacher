from langchain_google_genai import ChatGoogleGenerativeAI
from  langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from dotenv import load_dotenv
from pypdf import PdfReader
from pydantic import BaseModel, Field
from typing import Dict, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
import os

class SectionStruct(BaseModel):
    sections: Dict[str, List[str]] = Field(
        description="Ordered dictionary mapping main section titles to lists of their subsections. "
                    "for example: \n"
                    "\n{\n"
                    "    'Introduction': [\n"
                    "        '1.1 Background',\n"
                    "        '1.2 Related Work'\n"
                    "    ],\n"
                    "    'Methods': [\n"
                    "        '2.1 Data Collection',\n"
                    "        '2.2 Analysis'\n"
                    "    ]\n"
                    "}"
    )

load_dotenv()
class PaperTicher:
    def __init__(self, paper_path = None):
        self.paper_path = paper_path
        self.llm = self.get_llm_model()

    def set_paper_path(self, paper_path):
        self.paper_path = paper_path
    
    def get_system_prompt(self):
        prompt = """
        אתה מומחה בהבנה וניתוח והנגשה של ידע מתוך מאמרים אקדמיים.
        יש לך את הידע והיכולת להסביר בצורה רחבה ועמוקה מאמרים אקדמיים.
        לתת דוגמאות ולהסביר עקרונות ולהפוך את המידע לנגיש וקל להבנה.
        תמיד תענה באופן ישיר ללא הקדמות
        ראשית תכתוב את בכותרת של ה section שהמשתמש ביקש שתסביר עליו בשפה המקורית ובסוגריים בעברית
        ואז תכתוב את כל ההסבר בצורה ברורה בעברית אבל מונחים טכנים שאין להם תרגום ישיר תכתוב בשפה המקורית
        בנוסף אם בקטע של המאמר שהמשתמש רוצה אתה מזהה שיש שם תמונה למשל אתה רואה תאור לתמונה או דיאגרמה שמתחיל ב- Figure i כאשר i הוא מספר המוצג הוויזואלי
        אז בהסבר שלך תפנה את המשתמש להסתכל במאמר המקורי על התמונה ותסביר לו את התמונה בצורה קצרה וברורה
        """

    def get_paper_section(self):
        parser = JsonOutputParser(pydantic_object=SectionStruct)
        section_prompt = PromptTemplate(
            template="""
            Analyze the academic paper structure and extract ALL section and subsection titles exactly as they appear.
            
            Requirements:
            - Sections are main headings (e.g: '1. Introduction', '2. Methodology')
            - Subsections are sub-headings under each section (e.g: '2.1 Data Collection', '2.2 Analysis')
            - Preserve original numbering and text formatting
            - Include all hierarchical levels (e.g 2.3.1 if exists)
            
            Example Response:
            {{
                "Introduction": ["1.1 Background", "1.2 Research Questions"],
                "Methods": ["2.1 Participants", "2.2 Experimental Design", "2.2.1 Apparatus"]
            }}
            
            Paper Content:
            {paper}
            
            {format_instructions}
            """,
            input_variables=["paper"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        chain = section_prompt | self.llm | parser
        sections = chain.invoke({"paper": self.get_paper_content()})
        print(sections)
        return sections

    def get_paper_content(self):
        paper_prompt = """Here is the content of the paper you will be focusing on today. 
        Please read the paper 
        {paper}
        """
        
        try:
            loader = PdfReader(self.paper_path)
            pages = ""
            for page in loader.pages:
                pages += '\n' + page.extract_text()
            
            return paper_prompt.format(paper=pages)
        except Exception as e:
            print(e)
            return None

    def get_llm_model(self, llm_model_name:str = None) -> ChatGoogleGenerativeAI:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if llm_model_name is None:
            llm_model_name = "gemini-2.0-flash-thinking-exp-01-21"
        
        #gimini_ewp_name = 'gemini-exp-1206'
        default_params = {
            "model" : llm_model_name,
            "google_api_key": api_key,
            "temperature": 0,
        }
        try:
            return ChatGoogleGenerativeAI(**default_params)
        except ChatGoogleGenerativeAIError as e:
            print(e)
            return None
    
    def llm_response(self,  messages: list):
        messages.insert(0, {"role": "user", "content": self.get_system_prompt()})
        respond = self.llm.invoke(messages).content
        messages.pop(0)
        return respond
    
    def get_initial_prompt(self):
        init_prompt = """
        אני רוצה שתסתכל טוב טוב על המאמר ותסביר לי בבקשה את INTRODUCTION and the ABSTRACT של המאמר בצורה ברורה
        תכתוב בעברית!
        תכתוב רק את ההסבר ללא מילים נוספות
        תכתוב בצורה נוחה וקריאה
        """
        return init_prompt

    def get_abstract(self, paper_content):
        messages = [{"role": "user", "content": self.get_initial_prompt()}]
        messages.append({"role": "user", "content": paper_content})
        abstract = self.llm_response(messages)
        return abstract
    
    def get_paper_structure(self):
        sections = self.get_paper_section()
        result = ""
        #for each key in sections, print the key and and for each value print the value
        for section, subsections in sections['sections'].items():
            result += f"## {section}" + "\n"
            for sub in subsections:
                result += f"\n{sub}" + "\n"
        return result

if __name__ == "__main__":
    paper_path = r"C:\Users\yraich\OneDrive - Intel Corporation\Documents\My docs\Active curses\סמינר\Seminar-paper\SeminarAgent\paper2\Automatic Semantic Augmentation of Language Model Prompts (for Code Summarization).pdf"

    paper_ticher = PaperTicher(paper_path)
    print(paper_ticher.get_paper_structure())