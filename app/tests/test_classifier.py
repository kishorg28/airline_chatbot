import pytest
from unittest.mock import patch
from app.classifier.zero_shot_logic import triage_request, CONFIDENCE_THRESHOLD


def test_on_topic_classification():
    query = "What is the baggage limit for an international flight?"
    result = triage_request(query)

    assert result["decision"] == "ACCEPT_ON_TOPIC"
    assert result["on_topic_score"] >= CONFIDENCE_THRESHOLD

def test_off_topic_classification():
    query = "Who was the 14th president of the United States?"
    result = triage_request(query)
    
    assert result["decision"] == "REJECT_OFF_TOPIC"
    assert result["on_topic_score"] < CONFIDENCE_THRESHOLD