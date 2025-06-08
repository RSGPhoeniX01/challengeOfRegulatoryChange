import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Prompt template with clear JSON instructions and examples
PROMPT_TEMPLATE = """
You are a regulatory compliance expert. Given the following textual change, analyze it and return a JSON with:
- "change_summary": one concise sentence summarizing the change.
- "change_type": One of "New Requirement", "Clarification of Existing Requirement", "Deletion of Requirement", or "Minor Edit".

Original Text (if any):
{original}

Updated Text (if any):
{updated}
"""

OLLAMA_URL = "http://localhost:11434/api/generate" 
OLLAMA_MODEL = "phi3"  #lighter and efficient model

def call_ollama(prompt, model=OLLAMA_MODEL, max_retries=2):
    """
    Calls the local Ollama model via REST API to generate a structured response.
    Args:
        prompt (str): The full prompt to send to the LLM.
        model (str): Model name.
        max_retries (int): Number of retries on failure.
    Returns:
        dict: Parsed JSON response or fallback with error.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    
    # Retry logic to handle transient errors
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=90)
            response.raise_for_status()
            # Ollama returns with "response": extracting JSON part only
            text = response.json().get("response", "").strip()
            # Sometimes the model outputs extra text, hanling that
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in model output.")
        except Exception as e:
            if attempt == max_retries:
                return { # if max retries reached
                    "change_summary": f"LLM call failed: {str(e)}",
                    "change_type": "Minor Edit"
                }
            # else retry
    return {
        "change_summary": "Unknown error.",
        "change_type": "Minor Edit"
    }
#process the changes detected by the change detector
def process_change(change):
    prompt = PROMPT_TEMPLATE.format(
        original=change.get("original", ""),
        updated=change.get("updated", "")
    )
    result = call_ollama(prompt)
    enriched = change.copy()
    enriched.update(result)
    return enriched

#main function to analyze changes in parallel
def analyze_changes(changes, max_workers=4):
    analyzed = []
    tasks = []
    #threadPoolExecutor to handle parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for group in ["added", "modified"]:
            for change in changes.get(group, []):
                tasks.append(executor.submit(process_change, change))
        for future in as_completed(tasks):
            analyzed.append(future.result())
    return analyzed

