import torch
from transformers import pipeline

# --- Configuration ---
BART_MODEL = "facebook/bart-large-mnli"
ON_TOPIC_LABEL = "A request specifically for airline customer support regarding flights, bookings, or policies."
OFF_TOPIC_LABEL = "A question about science, history, entertainment, or other non-business topics."

CANDIDATE_LABELS = [
    ON_TOPIC_LABEL,
    OFF_TOPIC_LABEL
]
CONFIDENCE_THRESHOLD = 0.85

# --- Initialization ---
# This block runs once when the module is imported.
print(f"Initializing Zero-Shot Classifier: {BART_MODEL}...")
try:
    device = 0 if torch.cuda.is_available() else -1 
    
    classifier = pipeline(
        "zero-shot-classification",
        model=BART_MODEL,
        device=device
    )
    print("Classifier loaded successfully.")

except Exception as e:
    print(f"Error loading classifier: {e}")
    classifier = None

# --- Classification Function (The API for other modules) ---
def triage_request(user_input: str) -> dict:
    """
    Classifies the user input and determines the routing decision (ACCEPT or REJECT).
    """
    if not classifier:
        return {"input": user_input, "predicted_top_label": "ERROR", "on_topic_score": 0.0, "decision": "REJECT_ERROR"}

    # Run the classification
    result = classifier(user_input, CANDIDATE_LABELS, multi_label=False)
    
    # 1. Locate the score for the specific ON_TOPIC_LABEL
    try:
        on_topic_index = result['labels'].index(ON_TOPIC_LABEL)
        on_topic_score = result['scores'][on_topic_index]
    except ValueError:
        on_topic_score = 0.0
    
    # 2. Make the final decision based PURELY on the ON-TOPIC score threshold
    if on_topic_score >= CONFIDENCE_THRESHOLD:
        decision = "ACCEPT_ON_TOPIC"
    else:
        # Rejection occurs if the score for the ON-TOPIC label is below the threshold
        decision = "REJECT_OFF_TOPIC" 

    return {
        "input": user_input,
        "predicted_top_label": result['labels'][0], 
        "on_topic_score": round(on_topic_score, 4),
        "decision": decision,
        "threshold": CONFIDENCE_THRESHOLD # Include threshold for clarity
    }