import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage,SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Union
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Union
import traceback


from web_search_facebook import facebook_searcher
from web_search_insta import insta_search
from web_search_linkedin import linkedin_searcher

from facebook import facebook_ID_searcher
from instagram import Insta_ID_searcher
from linkedin import linkedin_ID_searcher

from langchain_openai import ChatOpenAI

load_dotenv()

class InputState(TypedDict):
    Actual_name: str
    last_known_location: Optional[str]
    last_known_work: Optional[str]
    extra_meta_data: Optional[Union[str, dict]]

class OverallState(TypedDict, total=False):
    input: InputState
    fb_id: Optional[str]
    insta_id: Optional[str]
    linkedin_id: Optional[str]
    fb_profile_data: Optional[dict]
    insta_profile_data: Optional[dict]
    linkedin_profile_data: Optional[dict]
    output: Optional[dict]

def fb_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Facebook'
    uid = facebook_searcher(query, state["input"])
    return {"fb_id": uid}

def insta_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Instagram'
    uid = insta_search(query, state["input"])
    return {"insta_id": uid}

def linkedin_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Linkedin'
    uid = linkedin_searcher(query, state["input"])
    return {"linkedin_id": uid}

def fb_scrape_node(state):
    search_id = state.get("fb_id")
    if search_id and search_id!="None":
      try:  
        profile_data = facebook_ID_searcher(search_id)
        return {"fb_profile_data": profile_data}
      except:
        return {"fb_profile_data": {}} 
    return {}

def insta_scrape_node(state):
    search_id = state.get("insta_id")
    if search_id and search_id!="None":
       try: 
        profile_data = Insta_ID_searcher(search_id)
        return {"insta_profile_data": profile_data}
       except:
        return {"insta_profile_data": {}}   
    return {}

def linkedin_scrape_node(state):
    search_id = state.get("linkedin_id")
    if search_id and search_id!="None":
       try: 
        profile_data = linkedin_ID_searcher(search_id)
        return {"linkedin_profile_data": profile_data}
       except:
        return {"linkedin_profile_data": {}}   
    return {}

def summarize_node(state):
    llm = ChatOpenAI(api_key=os.environ['OPEN_AI_API_KEY'], model='gpt-4.1')

    input_data = state["input"]
    fb = state.get("fb_profile_data")
    insta = state.get("insta_profile_data")
    linkedin = state.get("linkedin_profile_data")
    summarize_sys_message = f'''
     You are tasked to find the the person's last known location based on the dates mentioned 
     on various social media profile, thus sort the events based on the dates and then, find out 
     the most recent time along with the dates. 
'''
    summary_prompt = f"""
Given the following inputs:
- Name: {input_data['Actual_name']}
- Last Known Location: {input_data.get('last_known_location', 'Unknown')}
- Last Known Work: {input_data.get('last_known_work', 'Unknown')}
- Extra Metadata: {input_data.get('extra_meta_data', 'None')}
- Current Date: {input_data.get('Current_date', 'None')}

And scraped social data:
Facebook: {fb}
Instagram: {insta}
LinkedIn: {linkedin}

Summarize the person’s most recent location, activity, and risk level.
"""

    result = llm.invoke([SystemMessage(content=summary_prompt),HumanMessage(content=summary_prompt)])
    return {"output": {"summary": result.content}}


def control_id_fetch(state):
    branches = []
    if "fb_id" not in state or not state["fb_id"]:
        branches.append("fb_id_node")
    if "insta_id" not in state or not state["insta_id"]:
        branches.append("insta_id_node")
    if "linkedin_id" not in state or not state["linkedin_id"]:
        branches.append("linkedin_id_node")
    return branches if branches else ["scrape_control_node"]

def start_node(state):
    return state  # Just passes state forward

def build_graph():
    builder = StateGraph(OverallState)

    # Dummy start node
    builder.add_node("start_node", RunnableLambda(start_node))

    # ID nodes
    builder.add_node("fb_id_node", RunnableLambda(fb_id_node))
    builder.add_node("insta_id_node", RunnableLambda(insta_id_node))
    builder.add_node("linkedin_id_node", RunnableLambda(linkedin_id_node))

    # Scrape nodes
    builder.add_node("fb_scrape_node", RunnableLambda(fb_scrape_node))
    builder.add_node("insta_scrape_node", RunnableLambda(insta_scrape_node))
    builder.add_node("linkedin_scrape_node", RunnableLambda(linkedin_scrape_node))

    # Summarize
    builder.add_node("summarize_node", RunnableLambda(summarize_node))

    # Set entry point to start_node
    builder.set_entry_point("start_node")

    # Fan out to all 3 ID nodes
    builder.add_edge("start_node", "fb_id_node")
    builder.add_edge("start_node", "insta_id_node")
    builder.add_edge("start_node", "linkedin_id_node")

    # Each ID to its scraper
    builder.add_edge("fb_id_node", "fb_scrape_node")
    builder.add_edge("insta_id_node", "insta_scrape_node")
    builder.add_edge("linkedin_id_node", "linkedin_scrape_node")

    # All scrape nodes converge to summarization
    builder.add_edge("fb_scrape_node", "summarize_node")
    builder.add_edge("insta_scrape_node", "summarize_node")
    builder.add_edge("linkedin_scrape_node", "summarize_node")

    # Final
    builder.add_edge("summarize_node", END)

    return builder.compile()

# -------------------------
# Build LangGraph
# -------------------------
# def build_graph():
#     builder = StateGraph(OverallState)

#     # ID nodes
#     builder.add_node("fb_id_node", RunnableLambda(fb_id_node))
#     builder.add_node("insta_id_node", RunnableLambda(insta_id_node))
#     builder.add_node("linkedin_id_node", RunnableLambda(linkedin_id_node))

#     # Scrape nodes
#     builder.add_node("fb_scrape_node", RunnableLambda(fb_scrape_node))
#     builder.add_node("insta_scrape_node", RunnableLambda(insta_scrape_node))
#     builder.add_node("linkedin_scrape_node", RunnableLambda(linkedin_scrape_node))

#     # Summarize node
#     builder.add_node("summarize_node", RunnableLambda(summarize_node))

#     # --- ENTRY ---
#     builder.set_entry_point("fb_id_node")

#     # Conditional edges to prevent repeated ID search
#     builder.add_conditional_edges("fb_id_node", lambda state: "insta_id_node" if "insta_id" not in state else "linkedin_id_node")
#     builder.add_conditional_edges("insta_id_node", lambda state: "linkedin_id_node" if "linkedin_id" not in state else "fb_scrape_node")
#     builder.add_conditional_edges("linkedin_id_node", lambda state: "fb_scrape_node")

#     # Scraping step
#     builder.add_edge("fb_scrape_node", "insta_scrape_node")
#     builder.add_edge("insta_scrape_node", "linkedin_scrape_node")

#     # Final summarization
#     builder.add_edge("linkedin_scrape_node", "summarize_node")
#     builder.add_edge("summarize_node", END)

#     return builder.compile()


def start_node(state):
    return state  # Just passes state forward

def build_graph():
    builder = StateGraph(OverallState)

    # Dummy start node
    builder.add_node("start_node", RunnableLambda(start_node))

    # ID nodes
    builder.add_node("fb_id_node", RunnableLambda(fb_id_node))
    builder.add_node("insta_id_node", RunnableLambda(insta_id_node))
    builder.add_node("linkedin_id_node", RunnableLambda(linkedin_id_node))

    # Scrape nodes
    builder.add_node("fb_scrape_node", RunnableLambda(fb_scrape_node))
    builder.add_node("insta_scrape_node", RunnableLambda(insta_scrape_node))
    builder.add_node("linkedin_scrape_node", RunnableLambda(linkedin_scrape_node))

    # Summarize
    builder.add_node("summarize_node", RunnableLambda(summarize_node))

    # Set entry point to start_node
    builder.set_entry_point("start_node")

    # Fan out to all 3 ID nodes
    builder.add_edge("start_node", "fb_id_node")
    builder.add_edge("start_node", "insta_id_node")
    builder.add_edge("start_node", "linkedin_id_node")

    # Each ID to its scraper
    builder.add_edge("fb_id_node", "fb_scrape_node")
    builder.add_edge("insta_id_node", "insta_scrape_node")
    builder.add_edge("linkedin_id_node", "linkedin_scrape_node")

    # All scrape nodes converge to summarization
    builder.add_edge("fb_scrape_node", "summarize_node")
    builder.add_edge("insta_scrape_node", "summarize_node")
    builder.add_edge("linkedin_scrape_node", "summarize_node")

    # Final
    builder.add_edge("summarize_node", END)

    return builder.compile()

# -------------------------
# Flask API
# -------------------------
app = Flask(__name__)
CORS(app)

# Build the graph once at startup
graph = build_graph()

@app.route('/api/process', methods=['POST'])
def process_data():
    try:
        data = request.get_json()
        required_fields = ['field1', 'field2', 'field3', 'field4', 'field5']

        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        input_data = {
            "Actual_name": data['field1'],
            "last_known_location": data['field2'],
            "last_known_work": data['field3'],
            "extra_meta_data": f"{data['field4']} | Last seen date: {data['field5']}"
        }

        print("🔍 Running graph with:", input_data)

        try:
            result = graph.invoke({"input": input_data})
            print("✅ Graph result:", result)
        except Exception as ge:
            print("\n❌ ERROR INSIDE GRAPH ❌")
            traceback.print_exc()
            return jsonify({'success': False, 'error': f"Graph error: {str(ge)}"}), 500

        return jsonify({'success': True, 'result': result["output"]["summary"]})

    except Exception as e:
        print("\n❌ ERROR IN PROCESS_DATA ❌")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Prevent auto-restart so errors are visible
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
