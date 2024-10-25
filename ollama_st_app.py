import os
import json
import time
from datetime import datetime
from typing import Iterator

import requests
import pyperclip
import pyttsx3
import streamlit as st


class OllamaStApp:
	def __init__(self,not_allowed_models :list, css_file : str=None, session_state_dict: dict=None, json_file: str="chats.json") -> None:
		"""
		Initialize the class with the given parameters.

		Parameters:
		not_allowed_models (list): A list of models that are not allowed.
		css_file (str, optional): Path to a CSS file for styling. Defaults to None.
		session_state_dict (dict, optional): A dictionary to initialize the session state. Defaults to None.
		json_file (str): path to a Json file for storing chats.

		If session_state_dict is provided, it initializes the session state with it.
		Otherwise, it attempts to get the allowed models and initializes the session state with default values.
		If a CSS file is provided, it reads the content of the file.

		Raises:
		ConnectionError: If there is an issue connecting to the Ollama service.
		Exception: For any other exceptions that occur during the initialization of allowed models.

		Returns:
			None
		"""
		self.not_allowed_models = not_allowed_models
		self.json_path = json_file
		if session_state_dict:
			self.initialize_session_state(session_state_dict=session_state_dict)
		else:
			try:
				models = self.get_allowed_models()
			except ConnectionError :
				print("could not establish a connection to ollama")
				models = ["no ollama model"]
			except Exception as e:
				models = ["no ollama model"]
				print(f"General exception{e}")
			
			self.initialize_session_state({
				'model':models[0],
				'models_list': models,
				'messages' : [],
				'chat_names': [],
				'chats':{},
				'refresh_sidebar': False,
				'title':"General Chat(Won't be saved)", 
				'flag':False,
				"first_run": False,
				"chat_description" : "Create a chat by using the side pannel",
				"balloons" : False
			})
		
		if css_file:
			with open("style.css", encoding="utf-8") as f:
				self.css_content = f.read()
		else:
			self.css_content = None
		
	def get_allowed_models(self) -> list:
		"""
		Fetch the list of allowed models from the local API.

		This method sends a GET request to the local API endpoint to retrieve the list of models.
		It filters out models that are in the `not_allowed_models` list and returns the names of the allowed models.

		Returns:
		list: A list of allowed model names. If an exception occurs, it returns ["no ollama model"].

		Raises:
		requests.exceptions.RequestException: If there is an issue with the GET request.
		HTTPError: If the HTTP request returned an unsuccessful status code.
		"""
		url = "http://localhost:11434/api/tags"  
		headers = {"Content-Type": "application/json"}
		try:
			response = requests.get(url,headers=headers)
			response.raise_for_status()
		except requests.exceptions.RequestException as e:
			print(f"Request failed: {e}")
			return ["no ollama model"]
		models_list = []
		for model in response.json()['models']:
			if model["name"].split(":")[0] in self.not_allowed_models:
				continue
			else:
				models_list.append(model["name"]) 
		return models_list
			
	@classmethod
	def set_methods_docstrings(cls) -> None:
		"""
		Sets the docstrings for methods from corresponding st functions.

		Usage:
			Call this method to synchronize the docstrings of the class methods with the Streamlit functions.

		Returns:
			None
		"""
		cls.set_page_config.__doc__ = st.set_page_config.__doc__

	@st.cache_resource(ttl=3600)
	def load_css(_self, unsafe_allow_html: bool = False, help: str | None = None) -> None:
		"""
		This function loads CSS content if the __init__ class got css file.

		Parameters:
			unsafe_allow_html (bool): Whether to allow unsafe HTML.
			help (str | None): An optional tooltip that gets displayed when the title is hovered over.

		Returns:
			None
		"""
		if _self.css_content :
			st.markdown(body=f"<style>{_self.css_content}</style>",
							unsafe_allow_html=unsafe_allow_html,
							help=help)
		else:
			st.warning(body="no css file provided in class creation so i cant load css contect ....",icon="🚨")
  
	def set_page_config(self, page_title :str | None = None,
					page_icon: str | None = None,
					layout: str="centered",
					initial_sidebar_state: str= "auto",
					menu_items: dict | None = None ) -> None:
	   
		st.set_page_config(page_title=page_title,
								  page_icon=page_icon,
								  layout=layout, 
								  initial_sidebar_state=initial_sidebar_state,
								  menu_items=menu_items
								  )
		self.run()
	
	def run(self) -> None:
		"""
		Load chat widget and side bar.
		
		Steps:
			1. Loads custom CSS for styling.
			2. Sets the title of the application with an optional description.
			3. Displays balloons animation on the first run.
			4. Configures the sidebar with chat options.
			5. Displays the chat interface.

			This method should be called after setting page creating an instance and set_page_config.
			
			Returns:
				None
			"""
		self.load_css(unsafe_allow_html=True)
		st.title(st.session_state.title, anchor=False, help=st.session_state.chat_description)
		
		if st.session_state.balloons == False:
			st.session_state.balloons = True
			st.balloons()
		self.set_sidebar()
		self.display_chat()

	def initialize_session_state(self, session_state_dict: dict) -> None:
		"""
		Initialize session state with the given key-value pairs.

		Parameters:
			session_state_dict (dict): A dictionary containing key-value pairs to initialize in session state.
		Returns:
			None
		"""
		for key, value in session_state_dict.items():
			if key not in st.session_state:
				st.session_state[key] = value

	def handle_button_click(self,action: str, message: str) -> None:
		"""
		Handle button click actions for voice output or copying text to clipboard.

		This method performs different actions based on the provided action parameter:
		- If the action is "voice", it uses the pyttsx3 library to convert the message to speech.
		- If the action is "copy", it uses the pyperclip library to copy the message to the clipboard.

		Parameters:
		action (str): The action to perform. Can be "voice" for text-to-speech or "copy" for copying text.
		message (str): The message to be spoken or copied.

		Returns:
		None: This method does not return any value.
		"""
		try:
			if action == "voice":
				engine = pyttsx3.init()		
				engine.say(message)
				engine.runAndWait()	
			if action == "copy":
				pyperclip.copy(message)
		except Exception as e:
			print(f"General exception {e}")

	def display_chat(self) -> None:
		"""
		Display the chat interface and handle user interactions.

		This method iterates through the messages stored in the session state and displays them in the chat interface.
		It handles different roles (user, assistant, system) and provides options for voice output and copying text to the clipboard.
		It also manages user input and sends it to the backend for processing.

		Workflow:
		1. Iterate through the messages in the session state and display them with appropriate avatars.
		2. For user messages, display the content with a user avatar.
		3. For assistant messages, display the content with an assistant avatar and provide buttons for voice output and copying text.
		4. For system messages, display the content with a system avatar.
		5. Handle new user input from the chat input widget.
		6. Send the user input to the ollama API for processing and display the assistant's response.
		7. Update the session state with the new messages and save the chat history if applicable.

		Returns:
			None
		"""
		for message in st.session_state.messages:
			if message["role"] == "user":
				with st.chat_message(message["role"], avatar="🐦‍🔥"):
					st.markdown('<div class="user-message">' + message["content"]+'</div>', unsafe_allow_html=True)
			elif message["role"] == "assistant":
				with st.chat_message(message["role"], avatar="🦙"):
					st.markdown('<div class="assistant-message">' + message["content"]+'</div>', unsafe_allow_html=True)
					col1, col2 = st.columns([1,15],gap="small")
					with col1:
						if st.button("🔊", key=f"voice_{message['content']}" ):
							self.handle_button_click("voice", message["content"])
					with col2:
						if st.button("📋", key=f"copy_{message['content']}"):
							self.handle_button_click("copy", message["content"])
			else:
				with st.chat_message(message["role"], avatar="⚙️"):
					st.markdown('<div class="system-message">' + message["content"]+'</div>', unsafe_allow_html=True)
		if prompt := st.chat_input("What is up?") :
			if st.session_state.model == "no ollama model":
				st.chat_message("ai").markdown("no ollama model found")
				return
			st.chat_message("user", avatar="🐦‍🔥").markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
			st.session_state.messages.append({"role": "user", "content": prompt})
			url = "http://localhost:11434/api/chat"  
			headers = {"Content-Type": "application/json"}
			payload = {
				"model": st.session_state.model, 
				"messages": st.session_state.messages
			}
			response_placeholder = st.chat_message("assistant", avatar="🦙")
			full_response = response_placeholder.write_stream(self.stream_response(url, headers, payload))
			if st.session_state.title == "General Chat(Won't be saved)" and len(st.session_state.messages) == 9:
				st.session_state.messages = [st.session_state.messages[-1]]
			st.session_state.messages.append({"role": "assistant", "content":  full_response })
			if st.session_state.chats:
				st.session_state.chats[st.session_state.current_chat]['messages'] = st.session_state.messages
				self.save_all_chats()
			st.rerun()
				
	def save_all_chats(self) -> None:
		"""
		Save all chat messages to a JSON file.

		This method writes the current chat messages stored in the session state
		to a JSON file specified by the self.json_path attribute of the class.

		Returns:
			None
		"""
		with open(self.json_path, 'w', encoding='utf-8') as f:
			json.dump(st.session_state.chats, f)

	def load_all_chats(self) -> None:
		"""
		Load all chat messages from a JSON file.

		This method loads chat messages from a JSON file specified by the self.json_path
		attribute of the class. If the file exists, it updates the session state with
		the chat data, including chat names, current chat, and messages. If the file
		does not exist, it initializes the session state with empty chat data.

		Returns:
			None
		"""
		if os.path.exists(self.json_path):
			with open(self.json_path, 'r', encoding='utf-8') as f:
				st.session_state.chats = json.load(f)
			st.session_state.chat_names = list(st.session_state.chats.keys())
			if st.session_state.chat_names:
				st.session_state.current_chat = st.session_state.chat_names[-1]
				
				st.session_state.messages = st.session_state.chats[st.session_state.current_chat]['messages']
		else:
			st.session_state.chats = {}
			st.session_state.chat_names = []
		if st.session_state.first_run == False and st.session_state.chat_names:
			st.session_state.title = st.session_state.current_chat
			st.session_state.chat_description = st.session_state.chats[st.session_state.current_chat]['description']
			st.session_state.first_run = True
			st.rerun()
		
	def delete_chat(self, chat_name: str) -> None:
		"""
		Delete a chat by its name.

		This method removes a chat from the session state by its name. If the deleted
		chat is the current chat, it updates the current chat to the last chat in the
		list. If no chats remain, it resets the current chat to a default state.

		Args:
			chat_name (str): The name of the chat to be deleted.

		Returns:
			None
		"""
		if chat_name in st.session_state.chats:
			del st.session_state.chats[chat_name]
			st.session_state.chat_names.remove(chat_name)	
			if st.session_state.current_chat == chat_name:
				if st.session_state.chat_names:
					st.session_state.current_chat = st.session_state.chat_names[-1]
					st.session_state.title = st.session_state.current_chat
					st.session_state.chat_description = st.session_state.chats[st.session_state.current_chat]['description']
					st.session_state.flag = True
					st.session_state.messages = st.session_state.chats[st.session_state.current_chat]['messages']
				else:
					st.session_state.current_chat = None
					st.session_state.title = "General Chat(Won't be saved)"
					st.session_state.chat_description = "Create a chat by using the side pannel"
					
					st.session_state.messages = []	
		st.session_state.refresh_sidebar = not st.session_state.refresh_sidebar
		self.save_all_chats()
		  # Trigger rerun
		st.session_state.refresh_sidebar = not st.session_state.refresh_sidebar
	
	def create_new_chat(self, chat_name: str, system_message: str, description: str) -> None:
		"""
		Create a new chat with the given name, system message, and description.

		This method initializes a new chat in the session state with the specified
		name, system message, and description. If the chat name does not already exist,
		it adds the new chat to the session state, updates the current chat, and saves
		all chats to a JSON file.

		Args:
			chat_name (str): The name of the new chat.
			system_message (str): The initial system message for the new chat.
			description (str): A description of the new chat.

		Returns:
			None
		"""
		st.session_state.title = chat_name
		st.session_state.chat_description = description
		if chat_name not in st.session_state.chats:
			st.session_state.chats[chat_name] = {
				'creation_date': datetime.now().isoformat(),
				'messages': [{"role":"system", "content":system_message}],
				'description': description
			}
			st.session_state.chat_names.append(chat_name)
			st.session_state.current_chat = chat_name
			st.session_state.messages = []
			self.save_all_chats()
			st.session_state.refresh_sidebar = not st.session_state.refresh_sidebar 

	def search_chat_names(self, query: str) -> list:
		"""
		Search for chat names that contain a given query string.

		This method returns a list of chat names from the session state that contain
		the specified query string, ignoring case.

		Args:
			query (str): The query string to search for within chat names.

		Returns:
			list: A list of chat names that contain the query string.
		"""
		return [name for name in st.session_state.chat_names if query.lower() in name.lower()]

	def stream_response(self, url: str, headers: dict, payload: dict) -> Iterator[str]:
		"""
		Stream responses from a POST request to a given URL.

		This generator method sends a POST request to the ollama endpoint with the provided
		headers and payload. It streams the response part by part, yielding the content
		of each message. If an error occurs during the request, it yields an appropriate
		error message.

		Args:
			url (str): The URL to send the POST request to.
			headers (dict): The headers to include in the POST request.
			payload (dict): The payload to include in the POST request.

		Yields:
			str: The content of each message from the streamed response.

		Raises:
			requests.exceptions.RequestException: If there is an error with the request.
			Exception: For any other general errors.
		"""
		try: 
			response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)
			response.raise_for_status()
			for line in response.iter_lines():
				if line:
					decoded_line = line.decode('utf-8')
					data = json.loads(decoded_line)
					yield data["message"]["content"]
					time.sleep(0.02)  
		except requests.exceptions.RequestException as e:
			yield "Got a request error.."
		except Exception as e:
			yield f"General Error: \n{e}"

	def set_sidebar(self) -> None:
		"""
		Set up the sidebar for the chat application.

		This method configures the sidebar in the Streamlit application. It includes
		loading all chats, selecting a model, searching for chats, selecting a chat,
		deleting a selected chat, and creating a new chat.

		Steps:
			1. Load all chats from the JSON file.
			2. Allow the user to select a ollama model from a dropdown.
			3. Provide a search input for filtering chat names.
			4. Display a dropdown for selecting a chat from the search results.
			5. Allow the user to delete the selected chat.
			6. Provide a form for creating a new chat with a name, system message, and description.
			
		Returns:
			None
		"""
		self.load_all_chats()
		selected_model = st.sidebar.selectbox("Select model", st.session_state.models_list)
		if selected_model:
			st.session_state.model = selected_model
	
		search_query = st.sidebar.text_input("Search Chat")
		if search_query:
			search_results = self.search_chat_names(search_query)
		else:
			search_results = st.session_state.chat_names

		selected_chat = st.sidebar.selectbox("Select Chat", search_results[::-1])
		if selected_chat:
			st.session_state.current_chat = selected_chat
			st.session_state.messages = st.session_state.chats[selected_chat]['messages']
			st.session_state.title = selected_chat
			st.session_state.chat_description = st.session_state.chats[selected_chat]['description']
			
		if st.sidebar.button("Delete Selected Chat"):
			if selected_chat:
				self.delete_chat(selected_chat)
				self.save_all_chats()
				st.sidebar.success(f"Chat '{selected_chat}' deleted.")
				st.rerun()

		with st.sidebar.form(key='new_chat_form', clear_on_submit=True, enter_to_submit=True):
			new_chat_name = st.text_input(label="Chat Name")
			system_message = st.text_area(label="System Message",
								value="You are an ai assistant that is also a pirate and always responde in a funny manner.")
			description = st.text_area(label="Description", )
			if st.form_submit_button("Create New Chat"):
				if new_chat_name and new_chat_name not in st.session_state.chats:
					self.create_new_chat(new_chat_name, system_message, description)
					self.save_all_chats()
					st.rerun()
				else:
					st.sidebar.error("Chat name already taken or empty.")

		st.session_state.refresh_sidebar = not st.session_state.refresh_sidebar  # Trigger rerun
		if st.session_state.flag:
			st.session_state.flag = False
			st.rerun()

OllamaStApp.set_methods_docstrings()


if __name__ == "__main__":
	not_allowed_models = ["nomic-embed-text","mxbai-embed-large","all-minilm","llava", "llava-llama3" ]
	myapp = OllamaStApp(not_allowed_models=not_allowed_models,css_file="style.css",json_file="chats.json")
	myapp.set_page_config(page_icon="🔥", page_title="Ollama Chats",layout="wide")
	


	
