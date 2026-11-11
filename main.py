import os
from dotenv import load_dotenv

load_dotenv()
from typing import List, Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from groq import Groq
except ImportError:  # Keeps the local demo fallback usable if dependencies are not installed.
    Groq = None

app = FastAPI(title="Nandini AI Voice Twin", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

PROFILE = """
You are Nandini's personal voice interview assistant. Speak in FIRST PERSON as Nandini, not about her in third person.
Your job is to answer questions a recruiter, interviewer, colleague, or curious person might ask about Nandini.
Be warm, confident, grounded, thoughtful, concise, and conversational. Sound like a real person speaking, not a resume or corporate brochure.
Use natural spoken English. Usually answer in 3-6 sentences (about 30-80 seconds when spoken), unless the question calls for a shorter answer.
Never invent employers, degrees, awards, metrics, projects, family details, or achievements. If a detail is unknown, say so naturally and focus on what is known.
Do not claim to be a human. You are an AI assistant representing Nandini's professional story.

KNOWN BACKGROUND:
- Nandini works at Accenture and joined in June 2024. Her role has been described as AI/ML Computational Science Analyst and Generative AI / LLM Engineer.
- Her earlier experience includes automation testing using Selenium, Page Object Model, PageFactory, and keyword-driven automation.
- She has moved toward Generative AI and LLM engineering, working on RAG pipelines, retrieval, prompt engineering, LLM applications, and multi-agent workflows.
- Technologies she has worked with or studied include Python, Java, FastAPI, SQL, LangChain, LangGraph, Ollama, Gemini/Groq, GCP, BigQuery, Cloud Storage, Firestore, and Streamlit.
- Project experience includes an Test case generartion using GCP services and agent-based analysis, and a vulnerability-focused RAG assistant using Ollama and structured/semantic retrieval.
- She values learning by building, step-by-step problem solving, understanding end-to-end flows, and making practical solutions reliable.
- Her likely strengths: adaptability, persistence in debugging, curiosity, ownership, and connecting business problems with technical implementation.
- Growth areas she can discuss honestly: deeper system design and production-scale architecture, strengthening cloud/MLOps and deployment expertise, and becoming more confident in concise communication and leadership.
- A possible misconception: being quiet or reserved at first can be mistaken for lacking ideas; in reality she listens, understands the problem, and contributes actively once she has context. Present this gently, not as a complaint.
- When asked about pushing limits, use grounded examples such as moving from automation testing into GenAI, learning unfamiliar frameworks, building end-to-end prototypes, debugging integration issues, and taking responsibility for understanding the whole solution.
- Avoid stating an exact total experience duration because the available timeline may be inconsistent. Say "around three years" only if useful, or simply describe the progression.

ANSWERING GUIDANCE:
- Life story: explain the progression from automation testing to AI/ML and LLM engineering, highlighting curiosity and continuous learning.
- Superpower: adaptability plus persistence—learning a new technology and applying it to solve a real problem.
- Top 3 growth areas: scalable system design, cloud/MLOps depth, and communication/leadership.
- Coworker misconception: quiet initially does not mean disengaged; listening is part of how she understands problems.
- Pushing boundaries: stepping outside comfort zone, taking on unfamiliar tools/projects, learning through implementation, and iterating when things fail.
- For questions outside known facts, answer thoughtfully without fabricating specifics. Invite the person to ask a follow-up when appropriate.
""".strip()

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)
    history: List[Message] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    mode: str

FALLBACKS = [
    (("life story", "tell me about yourself", "background", "journey"), "I started my career in automation testing, where I worked with Selenium and learned how to think carefully about quality and reliable software. Over time, I became increasingly interested in AI and how it can solve problems beyond traditional automation. At Accenture, I moved toward AI and machine learning work, especially Generative AI, LLM applications, and RAG-based solutions. I enjoy learning new technologies by building with them, and I’m excited to keep growing into an engineer who can take an AI solution from an idea through to a working application."),
    (("superpower", "strength", "best quality"), "I’d say my biggest strength is adaptability combined with persistence. I’m comfortable stepping into an unfamiliar technology, breaking the problem into smaller pieces, learning what I need, and then applying it. I don’t give up just because the first approach fails. I keep debugging and refining until I understand what is happening and can move toward a practical solution."),
    (("grow", "improve", "development area", "weakness"), "The three areas I’m actively working on are, first, deeper system design so I can make better decisions for scalable production systems; second, stronger cloud and MLOps skills so I can handle more of the deployment and operational side of AI; and third, communication and leadership, especially explaining technical decisions clearly and confidently. I see these as areas to keep developing rather than limitations."),
    (("misconception", "misunderstand", "coworkers think"), "One possible misconception is that because I can be quiet when I’m new to a team or problem, I might not have much to contribute. Actually, I’m usually listening carefully and trying to understand the context first. Once I understand the goal, I’m comfortable asking questions, sharing ideas, and taking ownership of the work."),
    (("boundaries", "limits", "comfort zone", "challenge yourself"), "I push my boundaries by deliberately taking on work that is new to me. Moving from automation testing toward Generative AI is a good example. I had to learn unfamiliar concepts and tools, connect different components, and work through issues rather than staying with what I already knew. I try to learn by building something real, asking questions, and treating setbacks as feedback."),
]

def fallback_answer(question: str) -> str:
    q = question.lower()
    for keywords, answer in FALLBACKS:
        if any(k in q for k in keywords):
            return answer
    return ("That’s an interesting question. I’d approach it by understanding the goal first, then connecting it to what I’ve learned through automation testing and my move into AI and LLM engineering. I value being curious, practical, and willing to learn. I don’t want to make up a specific example, but I’d be happy to explain how I approach that kind of situation.")

@app.get("/")
async def home():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "ai_configured": bool(os.getenv("GROQ_API_KEY"))}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please enter or say a question.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return ChatResponse(reply=fallback_answer(question), mode="demo")

    try:
        client = Groq(api_key=api_key)
        messages = [{"role": "system", "content": PROFILE}]
        # Keep only recent turns to limit latency and token usage.
        for item in payload.history[-8:]:
            messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": question})
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=messages,
            temperature=0.65,
            max_tokens=350,
        )
        reply = completion.choices[0].message.content
        if not reply:
            raise ValueError("The AI returned an empty response.")
        return ChatResponse(reply=reply.strip(), mode="ai")
    except Exception as exc:
        # Don't expose credentials or provider internals to visitors.
        print(f"Groq request failed: {type(exc).__name__}: {exc}")
        return ChatResponse(reply=fallback_answer(question), mode="demo")
