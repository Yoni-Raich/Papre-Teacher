from langchain_google_genai import ChatGoogleGenerativeAI
from  langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from dotenv import load_dotenv
from pypdf import PdfReader
import os

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
        """



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
        

