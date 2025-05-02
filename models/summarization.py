import re
import spacy
from collections import Counter
from heapq import nlargest
from spacy.matcher import Matcher

# Load SpaCy model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

def preprocess_text(text):
    """Cleans the text by removing extra spaces, special characters, and fixing inconsistencies."""
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    text = re.sub(r'[^a-zA-Z0-9.,!?;\-]', ' ', text)  # Remove unwanted characters
    text = text.replace(" .", ".").replace(" ,", ",").replace(" ;", ";")  # Fix spacing issues
    text = text.strip()
    return text

def clean_extracted_items(items):
    """Filters out short or irrelevant extracted entities."""
    return {item for item in items if len(item) > 2 and not re.match(r'^[a-zA-Z]\.?$', item) and not item.isdigit()}

def extract_parties(doc):
    """Extracts parties involved in the case."""
    parties = {ent.text for ent in doc.ents if ent.label_ in {"PERSON", "ORG"}}
    legal_roles = re.findall(r"\b(Plaintiff|Defendant|Appellant|Respondent|Petitioner|Claimant|Accused|Complainant)\b", 
                             doc.text, re.IGNORECASE)
    parties.update(legal_roles)
    return clean_extracted_items(parties) or {"Not specified"}

def extract_case_laws(doc):
    """Extracts legal cases and references."""
    case_laws = {ent.text for ent in doc.ents if ent.label_ in {"LAW", "WORK_OF_ART"}}
    case_pattern = r"\b([A-Za-z]+ v\. [A-Za-z]+, \d+ [A-Za-z]+ \d+ \(\d{4}\))\b"
    case_laws.update(re.findall(case_pattern, doc.text))
    return clean_extracted_items(case_laws) or {"Not specified"}

def extract_jurisdiction(doc):
    """Extracts jurisdiction details from the text."""
    locations = {ent.text for ent in doc.ents if ent.label_ in {"GPE", "FAC"}}
    court_pattern = r"\b(?:Supreme Court|District Court|High Court|Court of Appeals) of [A-Za-z ]+\b"
    locations.update(re.findall(court_pattern, doc.text))
    return clean_extracted_items(locations) or {"Not specified"}

def extract_case_details(doc):
    """Extracts case metadata like involved parties, case laws, and jurisdiction."""
    return {
        "Parties Involved": ", ".join(sorted(extract_parties(doc))),
        "Case Laws Referenced": ", ".join(sorted(extract_case_laws(doc))),
        "Jurisdiction": ", ".join(sorted(extract_jurisdiction(doc))),
    }

def rank_sentences(doc, max_lines=10):
    """Ranks sentences for summarization using word importance and structure."""
    sentences = list(doc.sents)
    words = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    word_frequencies = Counter(words)

    entity_weights = {ent.text.lower(): 2 for ent in doc.ents if ent.label_ in {"ORG", "LAW", "GPE", "PERSON"}}
    sentence_scores = {}

    for i, sentence in enumerate(sentences):
        sentence_text = sentence.text.strip()
        sentence_length = len(sentence)

        # Avoid very short sentences
        if sentence_length > 5:
            score = sum(word_frequencies.get(token.text.lower(), 0) + entity_weights.get(token.text.lower(), 0)
                        for token in sentence)

            # Boost weight for early sentences
            position_weight = 1.2 if i < 2 else 1.0 / (i + 1)
            sentence_scores[sentence_text] = (score / sentence_length) * position_weight

    top_sentences = nlargest(max_lines, sentence_scores, key=sentence_scores.get)
    return sorted(top_sentences, key=lambda s: doc.text.index(s))

def summarize_text(text, max_lines=8):
    """Summarizes the given legal text into key points with clear formatting."""
    if not text or len(text.split()) < 50:
        return {
            "Parties Involved": "Not specified", 
            "Case Laws Referenced": "Not specified", 
            "Jurisdiction": "Not specified", 
            "Key Points": "The document text is too short to summarize."
        }
    
    text = preprocess_text(text)
    doc = nlp(text)
    case_details = extract_case_details(doc)
    key_sentences = rank_sentences(doc, max_lines)

    return {
        "Parties Involved": case_details["Parties Involved"],
        "Case Laws Referenced": case_details["Case Laws Referenced"],
        "Jurisdiction": case_details["Jurisdiction"],
        "Key Points": " ".join(key_sentences) + "."
    }
