from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify(text: str):
    labels = [
    "schedule_meeting",
    "check_schedule",
    "cancel_meeting",
    "update_meeting",
    ]

    classification = classifier(text, labels)
    
    return classification
