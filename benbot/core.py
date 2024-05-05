import json
import os
import requests

from dotenv import load_dotenv
from tinydb import Query

load_dotenv()


# TODO: implement the additional params for llms (temperature, max_tokens, etc.)
def run_llm(messages=[], model=os.getenv("LLM_MODEL", "TheBloke/stablelm-zephyr-3b-GGUF")):
    url = os.getenv("LLM_URL", "http://localhost:8080/v1") + "/chat/completions"
    token = os.getenv("LLM_TOKEN", "token")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "model": model,
        "messages": messages,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()["choices"][0]["message"]["content"]


# TODO: implement the additional params for llms (temperature, max_tokens, etc.)
def stream_llm(messages=[], model=os.getenv("LLM_MODEL", "TheBloke/stablelm-zephyr-3b-GGUF")):
    url = os.getenv("LLM_URL", "http://localhost:8080/v1") + "/chat/completions"
    token = os.getenv("LLM_TOKEN", "token")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "model": model,
        "messages": messages,
        "stream": True
    }

    print(json.dumps(data, indent=2))

    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

    for chunk in response.iter_lines(chunk_size=None):
        text = chunk.decode("utf-8")
        if text == "":
            continue
        if "data: [DONE]" in text:
            break
        if "data: " in text:
            text = text.split("data: ")[1]

        # debug:
        # yield f"```json\n{json.dumps(json.loads(text), indent=2)}\n```\n\n"

        try:
            data = json.loads(text)
            yield data["choices"][0]["delta"]["content"]
        except:
            continue



def get_session(session=None, db=None, create_if_not_exist=True):
    Session = Query()
    session_info = db.search(Session.name == session)
    if not session_info and create_if_not_exist:
        db.insert({
            "_type": "session",
            "name": session,
            "messages": [],
            "ltm": f"This is the first time I\'ve ever talked to this user."
        })
        session_info = db.search(Session.name == session)
    return session_info[0]


def update_session(session=None, db=None, messages=None, ltm=None):
    Session = Query()
    db.update({
            "messages": messages,
            "ltm": ltm
        },
        Session.name == session
    )


def rag(text, n_results=5, docs=None):
    results = docs.query(query_texts=[text], n_results=n_results)
    lines = ["# My Knowledge"]

    for idx, doc in enumerate(results["documents"][0]):
        lines.append(f"## From {results['metadatas'][0][idx]['url']} "
                     f"(paragraph {results['metadatas'][0][idx]['paragraph']})")
        lines.append(doc)
        lines.append("")

    return "\n".join(lines)
