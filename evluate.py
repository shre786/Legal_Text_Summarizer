from rouge import Rouge
from nltk.translate.bleu_score import sentence_bleu
from bert_score import score

def calculate_rouge(reference, candidate):
    rouge = Rouge()
    scores = rouge.get_scores(candidate, reference, avg=True)
    return scores

def calculate_bleu(reference, candidate):
    reference_tokens = reference.split()
    candidate_tokens = candidate.split()
    score = sentence_bleu([reference_tokens], candidate_tokens)
    return score

def calculate_bertscore(reference, candidate):
    P, R, F1 = score([candidate], [reference], lang="en")
    return {"Precision": P.mean().item(), "Recall": R.mean().item(), "F1": F1.mean().item()}

def evaluate_summary(reference, candidate):
    results = {
        "ROUGE": calculate_rouge(reference, candidate),
        "BLEU": calculate_bleu(reference, candidate),
        "BERTScore": calculate_bertscore(reference, candidate)
    }
    return results

# Example Usage
reference_summary = "On 9 August 2024, a 31-year-old female postgraduate trainee doctor at R. G. Kar Medical College and Hospital in Kolkata, West Bengal, India, was raped and murdered in a college building. Her body was found in a seminar room on campus. On 10 August 2024, a 33-year-old male civic volunteer, named Sanjoy Roy working for Kolkata Police was arrested under suspicion of committing the crime. Three days later, the Calcutta High Court, transferred the investigation to the Central Bureau of Investigation (CBI) stating that the Kolkata Police's investigation did not inspire confidence. The junior doctors in West Bengal undertook a strike action for 42 days demanding a thorough probe of the incident and adequate security at hospitals. The incident amplified debate about the safety of women and doctors in India, and has sparked significant outrage, and nationwide and international protests."
candidate_summary = "On 9 August, 2024, a thirty -one year old postgraduate doctor at RG Kar Medical College Hospital, Kolkata who was on a thirty six hour duty shift was murdered and allegedly raped inside the seminar room of the hospital. As horrific details have emerged in the course of media reportage, t he brutality of the sexual assault and the nature of the crime have shocked the conscience of the Nation. Writ petitions were instituted before the Calcutta High Court seeking among other things, a court -monitored investigation of the crime and the conduct of the hospital authorities, including the role of the Principal of the medical college and other officials by a special team of investigating officers. Medical Associations have consistently raised issues o f the lack of workplace safety in health care institutions. Hospitals and medical care facilities are open throughout the day and night. Medical professionals - doctors, nurses and paramedic staff - work round the clock. Such Page 4 of 16 allegations are immediately followed by violence against medical professionals."

results = evaluate_summary(reference_summary, candidate_summary)
print("Summary Evaluation Results:")
print(results)
