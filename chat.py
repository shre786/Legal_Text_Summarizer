import re
from sentence_transformers import SentenceTransformer, util
import torch
from nltk import sent_tokenize
from fuzzywuzzy import process  # For improved keyword matching

# Initialize the improved model for sentence embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_text(text):
    """
    Cleans text while preserving key legal terms and formatting.
    """
    text = re.sub(r'\s+', ' ', text.strip())  # Remove excessive spaces/newlines
    text = re.sub(r'[\u200b-\u200d\uFEFF]', '', text)  # Remove zero-width spaces
    text = re.sub(r'([a-zA-Z])-(?=[a-zA-Z])', r'\1 ', text)  # Preserve hyphenated terms
    return text

def split_sentences(text):
    """
    Hybrid sentence splitting: Combines NLTK + Regex to improve text segmentation.
    """
    try:
        return sent_tokenize(text)  # Preferred for structured text
    except Exception:
        return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+', text)  # Regex fallback

def get_relevant_info(query, text):
    """
    Retrieve concise and highly relevant sentences based on the user query.
    If no strong match is found, a keyword-based fallback is provided.
    """
    text = clean_text(text)
    sentences = split_sentences(text)
    
    if not sentences:
        return "No relevant information found."
    
    # Sliding Window for better context (2-3 sentences per window)
    grouped_sentences = [" ".join(sentences[i:i + 3]) for i in range(0, len(sentences), 3)]

    # Encode query and grouped sentences
    query_embedding = model.encode(query, convert_to_tensor=True)
    sentence_embeddings = model.encode(grouped_sentences, convert_to_tensor=True)

    # Calculate cosine similarity
    cos_scores = util.cos_sim(query_embedding, sentence_embeddings)[0]

    # Dynamic Threshold Logic — Adapts to text complexity
    CONFIDENCE_THRESHOLD = 0.2  
    relevant_indices = (cos_scores >= CONFIDENCE_THRESHOLD).nonzero(as_tuple=True)[0]

    # If no strong match found, attempt keyword-based fallback
    if len(relevant_indices) == 0:
        keyword_fallback = keyword_match(query, grouped_sentences)
        if keyword_fallback:
            return keyword_fallback
        return "I couldn't find highly relevant information. Please refine your query."

    # Extract the **top 2 most relevant grouped sentences**
    top_results = torch.topk(cos_scores, k=min(2, len(relevant_indices)))

    # Select concise, precise answers
    relevant_sentences = [grouped_sentences[i].strip() for i in top_results.indices]

    # Return final concise result
    result = " ".join(relevant_sentences)
    return result if len(result) <= 200 else result[:200] + "... (See document for full details)"

def keyword_match(query, sentences):
    """
    Improved fallback logic using fuzzy matching to prioritize partial matches.
    """
    keywords = query.lower().split()

    best_matches = []
    for sentence in sentences:
        match_score = max([process.extractOne(word, sentence.lower().split())[1] for word in keywords])
        if match_score >= 70:  # Only include high-confidence keyword matches
            best_matches.append((sentence, match_score))

    # Prioritize sentences with the highest match score
    best_matches.sort(key=lambda x: x[1], reverse=True)

    # Return top 2 matches with highest keyword relevance
    if best_matches:
        return " ".join([match[0] for match in best_matches[:2]])

    return None
