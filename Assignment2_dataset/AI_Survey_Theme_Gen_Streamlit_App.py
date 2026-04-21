#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import requests
import pandas as pd
import json
import re
import time
import streamlit as st

os.environ["HF_TOKEN"] = "your _token_here"
HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
    "Content-Type": "application/json"
}


# In[2]:



def call_llm(prompt):
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 400
    }

    for _ in range(5):  
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text[:200])
            time.sleep(3)
            continue

        try:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception:
            print("Bad response:", response.text[:200])
            time.sleep(3)

    return "[]"


# In[3]:


def extract_json(text):
    match = re.search(r"\[.*\]", text, re.S)
    if match:
        return match.group(0)
    return "[]"


# In[4]:


def get_responses(series):
    responses = []

    for val in series.dropna():
        if isinstance(val, str) and "|" in val:
            responses.extend([v.strip() for v in val.split("|")])
        else:
            responses.append(str(val))

    return responses


# In[10]:


def generate_themes(responses, n_themes=6):
    sample = responses[:10]

    prompt = f"""
You are analyzing qualitative survey responses.

Responses:
{sample}

Task:
Generate {n_themes} meaningful, non-overlapping themes.

Rules:
- Themes must be specific and data-driven
- Avoid generic words, never use 'general feedback as theme'
- Each theme should represent a distinct idea
- Keep themes short (3–6 words)

Return ONLY in given format:
["Theme 1: theme_name_1",
 "Theme 2: theme_name_2",
 .
 .
 .
 ]
"""

    output = call_llm(prompt)
    print(f"theme llm :{output}")

    try:
        clean = extract_json(output)
        return json.loads(clean)
    except:
        return ["General Feedback"]


# In[11]:


def map_responses_to_themes(responses, themes):
    sample = responses[:5]

    prompt = f"""
Responses:
{sample}

Themes:
{themes}

Task:
Assign relevant themes to each response.

Rules:
- Max 2 themes per response
- Only use given themes
- No new themes

Return JSON:
[
  {{"response": "...", "themes": ["Theme 1"]}},
  ...
]
"""

    output = call_llm(prompt)

    try:
        clean = extract_json(output)
        parsed = json.loads(clean)
#         print([x["response"] for x in parsed])
        return [x["response"] for x in parsed]
    except:
        return [[] for _ in sample]


# In[12]:


def run_thematic_analysis(df):
    results = {}

    ignore_cols = ["Respondent ID", "Name of Respondent", "State"]

    for col in df.columns:
        if col in ignore_cols:
            continue

        print(f"\nProcessing: {col}")

        responses = get_responses(df[col])

        if len(responses) == 0:
            continue

        # Step 1: Themes
        themes = generate_themes(responses, 6)
        print("Themes:", themes)

        # Step 2: Mapping (sample to save cost)
        mappings = map_responses_to_themes(responses, themes)
        print(mappings)

        results[col] = {
            "themes": themes,
            "sample_mappings": mappings
        }

    return results


# In[ ]:


# df=pd.read_excel('structured_output.xlsx')
# print(df.head())
# analysis = run_thematic_analysis(df)


# In[ ]:


# ------------------- UI -------------------
st.title("AI Survey Theme Analyzer")

uploaded_file = st.file_uploader("Upload structured Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Preview", df.head())

    ignore_cols = ["Respondent ID", "Name of Respondent", "State"]
    text_cols = [c for c in df.columns if c not in ignore_cols]

    selected_col = st.selectbox("Select question/section", text_cols)

    if st.button("Run Analysis"):
        responses = get_responses(df[selected_col])

        if not responses:
            st.error("No responses found")
        else:
            with st.spinner("Generating themes..."):
                themes = generate_themes(responses)

            st.success("Themes Generated")
            st.write(themes)

            with st.spinner("Mapping responses..."):
                mappings = map_responses_to_themes(responses, themes)

            st.write("### Sample Mappings")
            st.json(mappings[:5])


# In[ ]:





# In[ ]:




