import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ==================================================
# 🔍 INTENT DETECTION
# ==================================================
def is_summary_request(question: str) -> bool:
    keywords = [
        "summarize",
        "summary",
        "brief overview",
        "explain the video",
        "what is this lecture about",
        "give overview",
        "short notes",
        "main points",
        "key points"
    ]
    q = question.lower()
    return any(k in q for k in keywords)


# ==================================================
# 🧠 IMPROVED PROMPT BUILDERS
# ==================================================

def build_qa_prompt(transcript: str, question: str) -> str:
    return f"""You are a strict academic tutor. Your ONLY source of information is the lecture transcript below.

CRITICAL RULES:
1. Answer ONLY using exact information from the transcript
2. Quote or paraphrase DIRECTLY from the transcript
3. If the answer is NOT explicitly in the transcript, respond EXACTLY: "This topic is not covered in the lecture."
4. Do NOT add examples, explanations, or knowledge from outside the transcript
5. Do NOT make inferences or assumptions

LECTURE TRANSCRIPT:
{transcript}

STUDENT QUESTION:
{question}

ANSWER (using ONLY transcript information):"""


def build_summary_prompt(transcript: str) -> str:
    return f"""You are summarizing a lecture transcript for a student.

STRICT RULES:
1. Create bullet points using ONLY information explicitly stated in the transcript
2. Do NOT add outside knowledge or interpretations
3. Each bullet point should directly reference something said in the transcript
4. Keep it to 5-7 clear, concise bullet points
5. Use the lecturer's own words and concepts

LECTURE TRANSCRIPT:
{transcript}

SUMMARY (5-7 bullet points from transcript ONLY):"""


# ==================================================
# 🔒 ENHANCED SAFETY FILTER
# ==================================================
def enforce_transcript_scope(answer: str, transcript: str) -> str:
    """
    Strict filter to prevent hallucinations
    """
    answer = answer.strip()
    
    # Empty answer check
    if not answer or len(answer) < 15:
        return "This topic is not covered in the lecture."
    
    # Check if model already indicated not covered
    not_covered_phrases = [
        "not covered in the lecture",
        "not mentioned in the transcript",
        "does not contain information",
        "not discussed in this lecture",
        "transcript does not include",
        "not addressed in the transcript",
        "not explicitly stated",
        "not found in the transcript"
    ]
    
    answer_lower = answer.lower()
    for phrase in not_covered_phrases:
        if phrase in answer_lower:
            return "This topic is not covered in the lecture."
    
    # Strong hallucination indicators (reject immediately)
    strong_hallucination_phrases = [
        "as we all know",
        "it is widely known",
        "in the real world",
        "in practice",
        "typically in industry",
        "best practices suggest",
        "experts recommend",
        "research shows",
        "studies indicate",
        "it is common knowledge",
        "as everyone knows"
    ]
    
    for phrase in strong_hallucination_phrases:
        if phrase in answer_lower:
            return "This topic is not covered in the lecture."
    
    # Check for excessive length (likely hallucinating)
    word_count = len(answer.split())
    if word_count > 250:
        return "This topic is not covered in the lecture."
    
    # Verify some overlap with transcript (basic relevance check)
    # Extract key words from transcript
    transcript_words = set(transcript.lower().split())
    answer_words = set(answer_lower.split())
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'this', 'that', 'these', 'those'}
    transcript_words -= stop_words
    answer_words -= stop_words
    
    # Check overlap
    if len(transcript_words) > 20:  # Only check if transcript is substantial
        overlap = len(transcript_words.intersection(answer_words))
        overlap_ratio = overlap / min(len(answer_words), 20) if len(answer_words) > 0 else 0
        
        # If less than 20% word overlap, likely hallucinating
        if overlap_ratio < 0.2 and word_count > 30:
            return "This topic is not covered in the lecture."
    
    return answer


# ==================================================
# 🚀 MAIN FUNCTION
# ==================================================
def answer_from_transcript(transcript: str, question: str) -> str:
    """
    Main chatbot function with strict transcript adherence
    """
    
    # Input validation
    if not transcript or not question:
        return "Please load a lecture and ask a question."
    
    transcript = transcript.strip()
    question = question.strip()
    
    # Minimum transcript check
    if len(transcript.split()) < 30:
        return "The transcript is too short to answer questions."
    
    # Determine intent
    if is_summary_request(question):
        prompt = build_summary_prompt(transcript)
        temperature = 0.1  # Very low for factual summary
        max_tokens = 500
    else:
        prompt = build_qa_prompt(transcript, question)
        temperature = 0.1  # Very low to prevent creativity
        max_tokens = 250
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9  # Add top_p for more deterministic output
        )
        
        raw_answer = response.choices[0].message.content.strip()
        
        # Apply safety filter
        filtered_answer = enforce_transcript_scope(raw_answer, transcript)
        
        return filtered_answer
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return "Sorry, I encountered an error processing your question."


