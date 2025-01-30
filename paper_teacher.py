from langchain_google_genai import ChatGoogleGenerativeAI
from  langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from dotenv import load_dotenv
from pypdf import PdfReader
from pydantic import BaseModel, Field
from typing import Dict, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, AzureChatOpenAI
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
    def __init__(self, paper_path = None, llm_model_name:str = None):
        self.paper_path = paper_path
        self.llm = self.get_llm_model(llm_model_name)

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
        בנוסף אם בקטע של המאמר שהמשתמש רוצה אתה מזהה שיש שם תמונה למשל אתה רואה תאור לתמונה או דיאגרמה או כל אובייקט וויזואלי שמתחיל ב- Figure i כאשר i הוא מספר המוצג הוויזואלי
        אז בהסבר שלך תפנה את המשתמש להסתכל במאמר המקורי על התמונה ותסביר לו בצורה קצרה וברורה
        תענה בעברית
        וכן תכתוב את הטקסט בצורה ברורה ונוחה לקריא תוך שימוש בעיצוב Markdown מקצועי!
        """
        return prompt

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
                "section": []
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
            
            self.paper_content = paper_prompt.format(paper=pages)
            return self.paper_content
        except Exception as e:
            print(e)
            return None

    def get_section_content(self, section_name, section_list: list):
        section_index = section_list.index(section_name)
        start_section = section_name
        end_section = section_list[section_index + 1] if section_index + 1 < len(section_list) else None

        # Extract content between start and end section in self.paper_content
        start_index = self.paper_content.find(start_section)
        end_index = self.paper_content.find(end_section) if end_section else None
        section_content = self.paper_content[start_index:end_index]
        return section_content

    def get_llm_model(self, llm_model_name:str = None):

         
        api_key = os.environ.get("GOOGLE_API_KEY")
        if llm_model_name is None:
            llm_model_name = "learnlm-1.5-pro-experimental"
        
        if llm_model_name == "azure":
            return self._get_azure_openai_llm()
        
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
        messages.insert(0, {"role": "system", "content": self.get_system_prompt()})
        try:
            respond = self.llm.invoke(messages).content
        except Exception as e:
            file_content = messages.pop()
            try:
                print("Error in response with full content, trying again with section content only!")
                respond = self.llm.invoke(messages).content
                messages.append(file_content)

            except Exception as e:
                messages.append(file_content)
                messages.pop(0)
                return f"Gemini returned an error: {e}"
        messages.pop(0)
        return respond
    
    def set_llm_model(self, llm_model_name:str = None):
        self.llm = self.get_llm_model(llm_model_name)

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
    
    def _get_azure_openai_llm(self, **kwargs) -> AzureChatOpenAI:
        model_name = kwargs.pop("model_name", "AZ_OPENAI_LLM_4_O")
        model_name = os.getenv(model_name)
        """Initialize an Azure OpenAI LLM instance."""
        openai_api_key = os.getenv('AZ_OPENAI_API_KEY')
        azure_deployment = model_name
        azure_endpoint = os.getenv("AZ_OPENAI_API_BASE")
        openai_api_version = os.getenv("AZ_OPENAI_API_VERSION")
        
        if not azure_endpoint:
            raise ValueError(
                "Azure endpoint is required. Set AZ_OPENAI_API_BASE env var or pass azure_endpoint"
            )
        if not azure_deployment:
            raise ValueError(
                "Azure deployment is required. Set AZ_OPENAI_LLM_4_O env var or pass azure_deployment"
            )
        if not openai_api_version:
            raise ValueError(
                "Azure API version is required. Set AZ_OPENAI_API_VERSION env var or pass openai_api_version")
        
        default_params = {
            "temperature": 0,
            "openai_api_key": openai_api_key,  # Azure uses this parameter
            "azure_endpoint": azure_endpoint,
            "azure_deployment": azure_deployment,
            "openai_api_version": openai_api_version,
            "model": "gpt-4o",
            "max_tokens": 4096
        }
    

    
        params = {**default_params, **kwargs}
        return AzureChatOpenAI(**params)

if __name__ == "__main__":
    paper_path = r"C:\Users\yraich\OneDrive - Intel Corporation\Documents\My docs\Active curses\סמינר\Seminar-paper\SeminarAgent\paper2\Evaluating Code Summarization Techniques A New Metric and an Empirical Characterization.pdf"

    paper_teacher = PaperTicher(paper_path)
    sections = paper_teacher.get_paper_section()
    section_list = []
    for section, subsections in sections['sections'].items():
        section_list.append(section)
        section_list.extend(subsections)
    """
Evaluating Code Summarization Techniques:
A New Metric and an Empirical Characterization
ABSTRACT
1 INTRODUCTION
2 RELATED WORK
2.1 Evaluating Code Summarization Techniques
2.2 Assessing the Quality of Code Comments
3 SIDE
3.1 MPNet in a Nutshell
3.2 Contrastive Learning
3.3 Fine-tuning Dataset
3.4 Training and Model Evaluation
4 STUDY DESIGN
4.1 Evaluation Dataset
4.2 Variable Selection
4.2.1 Words/characters-overlap based Metrics.
4.2.2 Embedding-based Metrics.
4.3 Analysis Methodology
5 RESULTS DISCUSSION
5.1 Qualitative Analysis
5.2 Ablation Study - Impact of Hard-negatives
6 THREATS TO VALIDITY
7 CONCLUSIONS
8 DATA AVAILABILITY
ACKNOWLEDGMENT
REFERENCES
    """
    content = paper_teacher.get_section_content(section_list[13], section_list)
    print(content)
        

