# BenBot: A simple LLM + RAG library with persistence.
This library provides tools for interfacing with language model servers to generate and stream responses based on user input. It utilizes environmental configurations to manage API details and integrates TinyDB for local storage of user sessions. The library also includes a document retrieval system to enhance responses with contextual knowledge.

## Features
- **Language Model Communication**: Send and receive data from language models configured through environment variables.
- **Streaming API Responses**: Handle streaming responses for real-time interaction with language models.
- **User Session Management**: Manage user data using TinyDB, allowing for session persistence and retrieval.
- **Document Retrieval**: Enhance responses by integrating external document data into the conversation context.
- **Environment Configuration**: Use `.env` files to manage API tokens, model details, and endpoint URLs securely.


## Installation
Clone this repository and navigate into your project directory:
```bash
git clone https://your-repository-url.git
cd your-library-directory
```

Install the required packages:
```bash
pip3 install -r requirements.txt
```



## Usage
Before using the functions in this library, ensure that your .env file is set up with the necessary variables:

```bash
# .env
LLM_MODEL=TheBloke/stablelm-zephyr-3b-GGUF
LLM_URL=http://localhost:8080/v1
LLM_TOKEN=your_llm_token_here
```

### Example Usage

```python
from bot.core import run_llm, stream_llm, get_user, update_user

# Example of running a language model
response = run_llm(messages=[{"role": "user", "content": "Hello, world!"}])
print(response)

# Example of streaming responses from a language model
for response in stream_llm(messages=[{"role": "user", "content": "Stream this message"}]):
    print(response)

# Example of managing a user in TinyDB
db = TinyDB('_data/users.json')
user_info = get_user(user='username', db=db)
update_user(user='username', db=db, messages=[], ltm='Updated long-term memory content')
```

### Streamlit - Docker Example

Build the docker image:
```bash
docker build . -t benbot
```

Run the docker image. Be sure to mount a `_data` directory and set the environment variables file:
``` bash
docker run \
  --env-file ./.env \
  -p 8501:8501 \
  -v ./_data/streamlit_chat:/home/appuser/_data \
  benbot
```

## Examples

To run the examples, first install BenBot framework as a package from the root directory:
```bash
pip3 install -e .
```

_Note: the `-e` installs the BenBot module as in an editable state, so changes will be reflected in future invocations._

### Discord Bot (examples/discord_bot.py)
This Discord bot leverages advanced natural language processing to provide a responsive and contextually aware user experience. It uses a combination of TinyDB for local storage and ChromaDB for enhanced data handling, alongside an LLM (Large Language Model) to process and respond to user messages intelligently. The bot maintains a conversational long-term memory to improve interaction quality over time.

**To run the disord service:**
```bash
python3 examples/discord_bot.py
```

### Streamlit Chatbot with Paywall Functionality (examples/streamlit_chat.py)
This project features a web-based chatbot built with Streamlit that incorporates advanced natural language processing to engage with users interactively. The application uses ChromaDB and TinyDB for data management and dynamically generates responses through a language model.


**To run the streamlit widget:**
```bash
streamlit run examples/streamlit_chat.py
```

## Development
This project is open for development. You are welcome to contribute to improving it or customizing it for your needs.


## Roadmap
- [x] Switch `user` for a `session` token. The idea is that the application can support anonymous requests, which wouldn't include a "user" in the traditional sense, but still needs a unique identifier for persistence.
- [ ] Include a namespace feature for the services. By separating the local storage of TinyDB and ChromaDB into seperate namespaces we can run multiple instances with different spaces from the same folder location.
- [ ] Create a dockerfile to quickly spin up custom bots.
- [x] Move the `resources/embeddings.ipynb`, `st-widget.py` and `discord.py` implementations to an `examples` folder. These should be provided as examples, rather than official implementations. (also, `st-widget.py` should be `streamlit.py`...)
- [ ] Split `core` library into several different ones, maybe `llm`, `session`, and `docs`.
