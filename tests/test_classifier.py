# Import the triage_request function from the core module
from classifier.zero_shot_logic import triage_request 
from classifier.zero_shot_logic import CONFIDENCE_THRESHOLD # Import the threshold for printing

def run_tests():
    """Runs a fixed set of test queries against the classifier."""
    test_queries = [
        "What is the baggage limit for an international flight?",  # Should be ACCEPT
        "Can you tell me the weather forecast for tomorrow?",       # Should be REJECT
        "I need to change my seat on flight AA123.",              # Should be ACCEPT
        "Who was the 14th president of the United States?",       # Should be REJECT
        "Hi, I am traveling soon and need help."                  # Should be REJECT (Ambiguous)
    ]

    print("\n--- Testing Zero-Shot Classifier ---")
    print(f"ACCEPTANCE THRESHOLD: {CONFIDENCE_THRESHOLD}")
    print("-" * 40)

    for query in test_queries:
        # Call the imported function
        classification = triage_request(query)
        
        print(f"Input: {classification['input']}")
        print(f"Predicted Top Label: {classification['predicted_top_label']}") 
        print(f"On-Topic Score: {classification['on_topic_score']}")
        print(f"Decision: {classification['decision']}")
        print("-" * 40)

if __name__ == "__main__":
    run_tests()