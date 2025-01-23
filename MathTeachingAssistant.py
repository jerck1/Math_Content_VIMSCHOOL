import pandas as pd
import openai
class MathTeachingAssistant:
    def __init__(self, excel_file_path, Bibliography):
        # Read Excel file
        self.df = pd.read_excel(excel_file_path, sheet_name='MT 10TH')#, index_col='Week')
        #Source files
        self.bib=Bibliography
        # OpenAI Client setup (to be initialized with API key)
        self.client = None
        
        # Assistant setup
        self.assistant = None
        #API key
        self.api_key = None
        #Create thread (A single one for a week)
        self.thread = None
    def preprocess_dataframe(self):#excel_file_path):
        """
        Preprocess the Excel file to create a multi-index DataFrame
        Handles rows with Week information and subsequent detail rows
        """
        # Load the Excel file
        #excel_file_path = 'HIGHSCHOOL-SCOPE.xlsx'  # Replace with your file path
        file = self.df#pd.read_excel(excel_file_path, sheet_name='MT 10TH')#pd.read_excel(file_path)
        # Fill NaN cells in the "Week","Topic",... columns with the previous value
        file['Week'] = file['Week'].ffill()#fillna(method='ffill')
        file['Topic'] = file['Topic'].ffill()
        file['Strands'] = file['Strands'].ffill()
        file['Standards'] = file['Standards'].ffill()
        file.set_index(['Week', 'Topic'], inplace=True)      
        return file

    def setup_openai(self):
        """Setup OpenAI client and create assistant"""
	# API Key input widget
	# User would manually enter API key and click button
        self.api_key = input("Enter API key:")
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        x=input('Do you have an assistant (Y or N)')
        if(x=='Y'):
            assistant_id = input('Write assistant id')
            try:
                self.assistant = self.client.beta.assistants.retrieve(assistant_id)
                print(f"Retrieved existing assistant: {assistant_id}")
            except Exception as e:
                print(f"Error retrieving assistant: {e}")
                return None
        else:
           # Upload file
            with open(self.bib, 'rb') as pdf_file:
                file = self.client.files.create(
                    file=pdf_file,
                    purpose="assistants"
                )
            # Create assistant
            self.assistant = self.client.beta.assistants.create(
                name = "10th Grade Teacher",
                instructions="You're a 10th grade online teacher explaining to 15 y.o. students following the BEST math florida standards",
                model="gpt-4o-mini", #"gpt-4-turbo",
                tools=[{"type": "file_search"}])
    def create_thread(self):
        """Create a thread"""
        self.thread = self.client.beta.threads.create()    
    def run(self, user_prompt):
        """Run with given prompt"""
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=user_prompt
        )
        
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )
        
        # Wait for run completion (simplified)
        while run.status != "completed":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
        
        # Retrieve messages
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
#         print("MSJ content: ",messages.data[0].content[0].text.value)#[1].content)#.text.value)
#         print("MSJ type: ",type(messages.data[0].content[0].text.value))#.text
        return messages.data[0].content[0].text.value
    
    def save_to_tex(self, content, filename):
        """Save content to LaTeX file"""
        with open(filename, 'w') as f:
            f.write(content)
        print(f"Saved to {filename}")
    
    def process_interactions(self,week,title):
        '''Executes all of the functions required to create and process the output files'''
        self.create_thread()
        
        #title=self.df.index[0][1]
        # Interaction 1: Presentation Creation
        presentation_prompt = f"Create me a 10 slide presentation of {title} with BEST math objectives {str(self.df[['Standards','Enabling Objectives','Unnamed: 5']].loc['Week 1'])}. Whole output within a single html environment. Divide it in 5 sections (1st: intro, last: Summary). Show title (Each title inside a rectangle w color #0e647b and in a single page), short explanation, definition, theorem and/or examples (steps by step). After each section use section {{ page-break-after: always; padding: 20px; }}. Examples in latex format inside of \( \) or \[ \] and graphs using Geogebra commands. Tables if applicable, also if applicable, SI units, if degrees use ^\circ and currencies around the world. Summary using Mermaid mindmaps language. You might include a game or a resource related with topics. Examples in two columns."
        #print(presentation_prompt)
        presentation_output = self.run(presentation_prompt)
        self.save_to_tex(presentation_output, f'presentation_{week}.html')
        
        # Interaction 2: Workshop Assignment
        workshop_prompt = "Create me a workshop assignment with 7 questions and examples similar to all of those provided in this chat. Whole output within an article class latex environment. Show me equations in latex format inside of begin{{align*}}  end{{align*}} inline equations with $$, if tables use latex table and tabular. If the topic requires graphics or plots create them with Geogebra commands inside begin{{verbatim}} end{{verbatim}}. Show Google sheets commands only if topic is related with calculations. You might include a game or a resource related with topics.  SI units, if degrees use ^\circ."
        
        workshop_output = self.run(workshop_prompt)
        self.save_to_tex(workshop_output, f'workshop_{week}.tex')
        
        # Interaction 3: Multiple Choice Test
        test_prompt = "Create me a unique multiple choice test with 5 questions related to all of those provided in this chat. Whole output within an article class latex environment. Enumerate them with just the number of the question, choice options within{{enumarate}}[label=(\alph*)].Show me equations in latex format inside of begin{{align*}}  end{{align*}}, if tables use latex table and tabular. If the topic requires graphics or plots create them in Geogebra inside begin{{verbatim}} end{{verbatim}}. Show Google sheets commands only if topic is related with calculations. SI units, if degrees use ^\circ "
        
        test_output = self.run(test_prompt)
        self.save_to_tex(test_output, f'test_{week}.tex')
        # Interaction 4: Forum question
        forum_prompt = "Create me a pretty short forum question (might be conceptual) posted by a tutor regarding an extension/real life application or interesting fact of these topics. Applications could include any of: Daily life, physics, engineering, finance, music, sports, gaming. Include emojis in text"
        
        forum_output = self.run(forum_prompt)
        self.save_to_tex(forum_output, f'forum_{week}.txt')

        print("All interactions completed and outputs saved!")
