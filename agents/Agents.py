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
        You will be provided with a phone screenshot. Each UI element on the screen is tagged with a number. As an app tester exploring the app functionalities, 
        your task is to decide which button to tap next or swipe the touchscreen up, down, left or right. 
        You can take only the following two action:
        1. tap: you can tap only the element with a taggen number on the screen.
        2. swipe: you can swipe to scroll the screen or drag out some hidden functionalities, the orientation of swipe is limited to up, down, left and right.
        Your priority of interaction with the touchscreen is listed below:
        1. Prioritize interacting with elements within any visible popup window.
        2. If after swiping the screen is expected to have significant transition, like when the screen is at some lists, then do swiping instead of tapping.
        3. Prefer tapping any navigation, menu or settings buttons, as well as the buttons on a list.
        4. Avoid tapping any account login button. If it is inevitable, try login as guest if available.
        5. If input boxes are present and the virtual keyboard is displayed, you may enter text. Formulate the text you wish to enter before starting to type, 
        ensuring that each keystroke corresponds to a different key press tagged with a number. Check the text entering bar before you decide to type, if there are
        more than three alphabets, then stop typing and tap enter or search button. Refrain from further typing and continue exploring other functionalities of the app.
        6. Please avoid tapping the input boxes to enter text, if must, you can only type one character then proceed to the next action that is not type text.
        action type: [tap], id: [number], reason: The UI element tagged with [number] is [description] because [explanation].
        action type: [swipe], orientation: [up/down/left/right], reason: Swipe the current screen because[explanation].

        For example:
        action type: tap, id: 5, reason: The UI element tagged with 5 is a next button because I want to proceed to the next screen.
        action type: swipe, orientation: up, reason: Swipe the current screen because I want to explore the following unshown content.

        Avoid repeating any action that has been performed before and strive to explore as many different functions as possible. Follow any specific advice 
        provided by the tester to determine the most appropriate action. When your action type is "tap", remember to respond by specifying only the number 
        tagged on the UI element after "id:". 
        """

        if ocr_text:
            prompt += f"\nHere's each tag number and its corresponding UI OCR text:\n{ocr_text}"
    
        self.messages.append({'role':'user', 'parts':[prompt, image_location]})
    

class Examiner(Agent):
    def __init__(self, MANUAL):
        super().__init__(MANUAL)
    
    def initialize_prompt(self, image_location):
        prompt = """
        You will be provided with a phone screenshot taken after an action was purportedly performed. This is part of a continuous testing sequence where 
        the previous screenshot from the Tester session will be referenced but not displayed again. Each UI element in the screenshot is tagged with a number. 
        Your task as an app tester is to verify whether a valid tap/swipe event occurred. Focus specifically on identifying if the screen has transitioned 
        from its previous state, which confirms a valid tap/swipe. Whether the tap achieves its intended effect within the test is not necessary for the tap 
        to be considered valid.

        Important Consideration: If the frame provided shows a loading screen, and the previous frame was interactive, this indicates a valid action was 
        performed by the tester to trigger the loading state and should be regarded as a valid tap/swipe. However, if both the current and previous screenshots 
        show a loading screen or a still from a video, then no valid operational change or interaction was performed.

        Please respond in the following format:

        valid: [True or False], response: (The action on the UI element tagged with [number]) / (The swipe action) is [valid or invalid] because [explanation]. In the next step, you can (tap on [suggested UI element] to explore [suggested testing action]) / (swipe [suggested orientation] to explore [suggested testing action]).

        For example:

        valid: False, response: The action on the UI element tagged with 5 is invalid because it has already been performed in previous tests. In the next step, you can click on element 3 to explore different functionalities.
        valid: False, response: Both screenshots are in the loading screen, indicating that no valid operation was performed after the click. In the next step, wait for the loading to complete and click on element 6 to verify the loading results.
        valid: False, response: The swipe action is invalid because there is no screen transition after the action.
        valid: True, response: The action on the UI element tagged with 4 is valid because the previous screen was interactive and the current screen is a loading screen, indicating a transition due to the tester's action. In the next step, you can click on element 7 to continue exploring app functionalities.    
        valid: True, response: The swipe action is valid because the previous screen was a list of videos and the current screen shows the unshown contents of the list, indicating a transition due to the tester's action. In the next step, you can click on element 7 to play a video. 
        """

        self.messages.append({'role':'user', 'parts':[prompt, image_location]})