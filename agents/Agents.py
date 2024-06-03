import google.generativeai as genai
import PIL.Image
import json
import os

SAFTY = {
    'HARM_CATEGORY_HARASSMENT': 'block_none',
    'HARM_CATEGORY_HATE_SPEECH': 'block_none',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none',
}

GENECONFIG = genai.types.GenerationConfig(
        candidate_count=1,
        temperature=1.0)

class Agent:
    def __init__(self, MANUAL):
        self.MANUAL = MANUAL
    
    def initialize_prompt(self, image_location):
        # This method should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement initialize_prompt method")
    
    def preprocess_messages(self):
        preprocessed_messages = []
        for message in self.messages:
            role = message['role']
            parts = message['parts']
            new_parts = parts[:]
            if role == 'user':
                for i, part in enumerate(parts):
                    if os.path.exists(part):
                        new_parts[i] = PIL.Image.open(part)
            preprocessed_messages.append({'role':role, 'parts':new_parts})
        return preprocessed_messages

    def send_prompt_to_VLM(self, apikey, model_name='models/gemini-1.5-flash-latest'):
        while True:
            try:
                preprocessed_messages = self.preprocess_messages()
                genai.configure(api_key=apikey)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(preprocessed_messages, safety_settings=SAFTY, generation_config=GENECONFIG)
                self.messages.append({'role':'model', 'parts':[response.text]})
                return response.text
            except Exception as e:
                print(e)
                continue
        
    def remove_previous_messages(self):
        if len(self.messages) > 0:
            self.messages = self.messages[:-1]
    
    def read_messages(self, new_message):
        self.messages = new_message
    
    def get_messages(self):
        return self.messages

class Tester(Agent):
    def __init__(self, MANUAL):
        super().__init__(MANUAL)

    def initialize_prompt(self, image_location, ocr_text):
        prompt = """
        You will be provided with a phone screenshot. Each UI element on the screen is tagged with a number. As an app tester exploring the app functionalities, your task is to decide which button to press next. Prioritize interacting with elements within any visible popup window. Additionally, if input boxes are present and the virtual keyboard is displayed, you may enter text. Formulate the text you wish to enter before starting to type, ensuring that each keystroke corresponds to a different key press tagged with a number. You are limited to entering a maximum of three characters per testing session, and these characters should be chosen randomly. After three keystrokes, you must refrain from further typing and continue exploring other functionalities of the app.
        If the app requires logging in, please attempt to log in using Gmail. If there is an option to log in as a guest, prefer that method instead.
        id: [number], reason: The UI element tagged with [number] is [description] because [explanation].

        For example:
        id: 5, reason: The UI element tagged with 5 is a next button because I want to proceed to the next screen.

        Avoid repeating any action that has been performed before and strive to explore as many different functions as possible. Follow any specific advice provided by the tester to determine the most appropriate action. Remember to respond by specifying only the number tagged on the UI element after "id:".
        """
        if ocr_text:
            prompt += f"\nHere's each tag number and its corresponding UI OCR text:\n{ocr_text}"
    
        self.messages.append({'role':'user', 'parts':[prompt, image_location]})
    

class Examiner(Agent):
    def __init__(self, MANUAL):
        super().__init__(MANUAL)
    
    def initialize_prompt(self, image_location):
        prompt = """
        You will be provided with a phone screenshot taken after an action was purportedly performed. This is part of a continuous testing sequence where the previous screenshot from the Tester session will be referenced but not displayed again. Each UI element in the screenshot is tagged with a number. Your task as an app tester is to verify whether a valid click event occurred. Focus specifically on identifying if the screen has transitioned from its previous state, which confirms a valid click. Whether the click achieves its intended effect within the test is not necessary for the click to be considered valid.

        Important Consideration: If the frame provided shows a loading screen, and the previous frame was interactive, this indicates a valid action was performed by the tester to trigger the loading state and should be regarded as a valid click. However, if both the current and previous screenshots show a loading screen or a still from a video, then no valid operational change or interaction was performed.

        Please respond in the following format:

        valid: [True or False], response: The action on the UI element tagged with [number] is [valid or invalid] because [explanation]. In the next step, you can click on [suggested UI element] to explore [suggested testing action].

        For example:

        valid: False, response: The action on the UI element tagged with 5 is invalid because it has already been performed in previous tests. In the next step, you can click on element 3 to explore different functionalities.
        valid: False, response: Both screenshots are in the loading screen, indicating that no valid operation was performed after the click. In the next step, wait for the loading to complete and click on element 6 to verify the loading results.
        valid: True, response: The action on the UI element tagged with 4 is valid because the previous screen was interactive and the current screen is a loading screen, indicating a transition due to the tester's action. In the next step, you can click on element 7 to continue exploring app functionalities.    
        """

        self.messages.append({'role':'user', 'parts':[prompt, image_location]})