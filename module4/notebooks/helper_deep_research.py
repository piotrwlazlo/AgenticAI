import os
import json  
from datetime import datetime  
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.rule import Rule
from typing import List, Optional, Union, Literal, Annotated
from pydantic import BaseModel, Field
from annotated_types import MinLen, MaxLen
import helper as h
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(
    api_base_url = "https://llm-api.dataworkshop.eu",
    api_key = os.getenv("OPENAI_API_KEY")
)


console = Console()
print = console.print



DOMAIN_PRESETS = {
    "academic": ["arxiv.org", "scholar.google.com", "semanticscholar.org", "openreview.net", "aclanthology.org"],
    "developer": ["github.com", "stackoverflow.com", "dev.to", "medium.com"],
    "community": ["news.ycombinator.com", "reddit.com", "twitter.com"],
    "official": ["openai.com", "anthropic.com", "google.ai", "microsoft.com/research", "huggingface.co"],
    "news": ["techcrunch.com", "theverge.com", "wired.com", "arstechnica.com", "venturebeat.com"],
}


# ═══════════════════════════════════════════════════════════════════════════════
#                      STRATEGICZNA DEKOMPOZYCJA
# ═══════════════════════════════════════════════════════════════════════════════

class ResearchDimension(BaseModel):
    """Wymiar badawczy - aspekt tematu do zbadania"""
    name: str = Field(..., description="Nazwa wymiaru, np. 'Technical Architecture'")
    description: str = Field(..., description="Co ten wymiar obejmuje")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Priorytet eksploracji"
    )
    source_types: List[Literal["academic", "developer", "community", "official", "news", "general"]] = Field(
        ..., description="Jakie typy źródeł są najlepsze dla tego wymiaru"
    )

    
class SubQuestion(BaseModel):
    """Konkretne pytanie do zbadania"""
    id: str = Field(..., description="Unikalny identyfikator, np. Q1, Q2")
    question: str = Field(..., description="Pytanie badawcze")
    search_query: str = Field(..., description="Zoptymalizowane zapytanie do wyszukiwarki")
    dimension: str = Field(..., description="Do którego wymiaru należy")
    source_type: Literal["academic", "developer", "community", "official", "news", "general"]
    status: Literal["pending", "in_progress", "completed", "spawned"] = "pending"
    parent_question_id: Optional[str] = Field(None, description="ID pytania, z którego to wynikło")

class ResearchPlan(BaseModel):
    """Pełny plan badawczy"""
    dimensions: List[ResearchDimension]
    questions: List[SubQuestion]
    estimated_depth: Literal["surface", "moderate", "deep", "exhaustive"]
    max_iterations: Annotated[int, Field(default=10, ge=3, le=20)]
        

class Finding(BaseModel):
    """Pojedyncze odkrycie z wyszukiwania"""
    content: str = Field(..., description="Treść odkrycia")
    source_url: str
    source_title: str
    relevance_score: float = Field(..., ge=0, le=1)
    question_id: str = Field(..., description="ID pytania, na które to odpowiada")
    finding_type: Literal["fact", "opinion", "statistic", "quote", "definition"]

        
        
class KnowledgeState(BaseModel):
    """Stan wiedzy - co już wiemy"""
    confirmed_facts: List[str] = Field(default_factory=list, description="Potwierdzone fakty")
    hypotheses: List[str] = Field(default_factory=list, description="Hipotezy do weryfikacji")
    contradictions: List[str] = Field(default_factory=list, description="Znalezione sprzeczności")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Zidentyfikowane luki")
    key_entities: List[str] = Field(default_factory=list, description="Kluczowe byty (osoby, firmy, technologie)")
        


def decompose_query(user_query: str) -> ResearchPlan:
    """
    Rozbija zapytanie użytkownika na wielowymiarowy plan badawczy.
    To jest "mózg" strategiczny - określa CO badać.
    """

    system_prompt = """Jesteś ekspertem od projektowania badań (Research Design Expert).

Twoim zadaniem jest przekształcić zapytanie użytkownika w kompleksowy plan badawczy.

ZASADY:
1. Zidentyfikuj 3-5 WYMIARÓW tematu (np. techniczny, praktyczny, społecznościowy, naukowy, przyszłościowy)
2. Dla każdego wymiaru określ najlepsze typy źródeł
3. Wygeneruj 5-8 konkretnych PYTAŃ BADAWCZYCH (SubQuestions)
4. Każde pytanie musi mieć zoptymalizowane search_query (bez słów "jak", "dlaczego" - same keywords)
5. Rozłóż pytania równomiernie między wymiary
6. Priorytetyzuj - nie wszystko jest równie ważne

TYPY ŹRÓDEŁ:
- academic: arxiv, scholar - dla fundamentów teoretycznych
- developer: github, stackoverflow - dla praktycznych rozwiązań
- community: hackernews, reddit - dla opinii i dyskusji
- official: strony firm, dokumentacje - dla oficjalnych informacji
- news: techcrunch, verge - dla aktualności
- general: ogólne wyszukiwanie

FORMAT PYTAŃ:
- Q1, Q2, Q3... - jako identyfikatory
- Pytania muszą być konkretne i możliwe do zbadania
- search_query musi być zoptymalizowane pod wyszukiwarki"""

    user_prompt = f"""Zapytanie użytkownika: "{user_query}"

Stwórz kompleksowy plan badawczy. Pamiętaj:
- Wymiary muszą pokrywać różne aspekty tematu
- Pytania muszą być konkretne i actionable
- search_query to NIE pytanie, to KEYWORDS do wyszukiwarki
- Określ głębokość jako: surface/moderate/deep/exhaustive"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


    return h.call_api(messages, ResearchPlan)        
        
        
# ═══════════════════════════════════════════════════════════════════════════════
#                      STRUKTURY DANYCH - RAPORT KOŃCOWY
# ═══════════════════════════════════════════════════════════════════════════════

class SourceCitation(BaseModel):
    """Cytowanie źródła"""
    id: int
    title: str
    url: str
    relevance: str


class ReportSection(BaseModel):
    """Sekcja raportu"""
    title: str
    content: str
    citations: List[int] = Field(default_factory=list, description="IDs cytowanych źródeł")


class FinalReport(BaseModel):
    """Kompletny raport badawczy"""

    executive_summary: str = Field(
        ...,
        description="Executive summary w 3-5 zdaniach"
    )

    key_findings: Annotated[List[str], MinLen(3), MaxLen(10)] = Field(
        ...,
        description="Kluczowe odkrycia jako bullet points"
    )

    detailed_sections: List[ReportSection] = Field(
        ...,
        description="Szczegółowe sekcje raportu"
    )

    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Co jeszcze warto zbadać"
    )

    contradictions_and_debates: List[str] = Field(
        default_factory=list,
        description="Sprzeczności i otwarte debaty w temacie"
    )

    sources: List[SourceCitation]

    confidence_level: Literal["high", "medium", "low"] = Field(
        ...,
        description="Poziom pewności na podstawie jakości źródeł"
    )

    research_metadata: dict = Field(
        default_factory=dict,
        description="Metadane: czas, liczba iteracji, liczba źródeł"
    )        
        
        
# ═══════════════════════════════════════════════════════════════════════════════
#                      ResearchState - ADAPTACYJNE PLANOWANIE
# ═══════════════════════════════════════════════════════════════════════════════

class ResearchState:
    """
    Stan całego procesu badawczego.
    To jest "pamięć robocza" agenta.
    """

    def __init__(self, plan: ResearchPlan, user_query: str):
        self.user_query = user_query
        self.plan = plan
        self.knowledge = KnowledgeState()
        self.findings: List[Finding] = []
        self.iteration = 0
        self.plan_history: List[dict] = []  # Historia zmian planu
        self.action_log: List[str] = []

    def get_pending_questions(self) -> List[SubQuestion]:
        return [q for q in self.plan.questions if q.status == "pending"]

    def get_completed_questions(self) -> List[SubQuestion]:
        return [q for q in self.plan.questions if q.status == "completed"]

    def mark_question_completed(self, question_id: str):
        for q in self.plan.questions:
            if q.id == question_id:
                q.status = "completed"
                break

    def add_question(self, question: SubQuestion):
        self.plan.questions.append(question)

    def log_plan_state(self):
        """Zapisz snapshot planu dla śledzenia ewolucji"""
        snapshot = {
            "iteration": self.iteration,
            "pending_count": len(self.get_pending_questions()),
            "completed_count": len(self.get_completed_questions()),
            "total_findings": len(self.findings),
            "knowledge_facts": len(self.knowledge.confirmed_facts),
            "knowledge_gaps": len(self.knowledge.knowledge_gaps)
        }
        self.plan_history.append(snapshot)
        
        
    
def build_sgr_prompt(state: ResearchState) -> str:
    """
    Buduje dynamiczny prompt dla SGR na podstawie stanu.
    To jest "świadomość sytuacyjna" agenta.
    """
    
    # Status pytań
    pending = state.get_pending_questions()
    completed = state.get_completed_questions()
    
    questions_status = "\n".join([
        f"  {'✅' if q.status == 'completed' else '⏳' if q.status == 'in_progress' else '📋'} "
        f"[{q.id}] {q.question[:60]}... ({q.source_type})"
        for q in state.plan.questions[:10]  # Limit dla kontekstu
    ])
    
    # Ostatnie findings
    recent_findings = state.findings[-5:] if state.findings else []
    findings_text = "\n".join([
        f"  • {f.content[:150]}... (źródło: {f.source_title[:30]})"
        for f in recent_findings
    ]) if recent_findings else "  Brak jeszcze odkryć"
    
    # Stan wiedzy
    knowledge_text = f"""
  Potwierdzone fakty: {len(state.knowledge.confirmed_facts)}
  Hipotezy: {len(state.knowledge.hypotheses)}
  Sprzeczności: {len(state.knowledge.contradictions)}
  Luki w wiedzy: {len(state.knowledge.knowledge_gaps)}
  Kluczowe byty: {', '.join(state.knowledge.key_entities[:5]) if state.knowledge.key_entities else 'brak'}"""
    
    # Postęp
    progress_pct = (len(completed) / len(state.plan.questions) * 100) if state.plan.questions else 0
    
    return f"""Jesteś Research Agentem prowadzącym głęboki research na temat:
<user_query>    
"{state.user_query}"
</user_query>

═══════════════════════════════════════════════════════════════════════════════
# STATUS BADANIA (Iteracja {state.iteration}/{state.plan.max_iterations})
═══════════════════════════════════════════════════════════════════════════════

POSTĘP: {progress_pct:.0f}% ({len(completed)}/{len(state.plan.questions)} pytań)

## PYTANIA:
<questions_status>
{questions_status}
</questions_status>

## OSTATNIE ODKRYCIA:
<findings_text>
{findings_text}
</findings_text>

## STAN WIEDZY:
<knowledge_text>
{knowledge_text}
</knowledge_text>

<task>
═══════════════════════════════════════════════════════════════════════════════
# TWOJE ZADANIE
═══════════════════════════════════════════════════════════════════════════════

## Przeanalizuj sytuację i zdecyduj o NASTĘPNYM KROKU:
<steps>
1. `execute_search` - Wykonaj wyszukiwanie dla konkretnego pytania (podaj question_id)
2. `spawn_question` - Wygeneruj NOWE pytanie, które wynikło z odkryć
3. `update_knowledge` - Zaktualizuj stan wiedzy na podstawie findings
4. `recalibrate_plan` - Zmień priorytety pytań
5. `conclude` - Zakończ research (jeśli mamy wystarczająco danych)
</steps>

## ZASADY:
<rules>
- Nie powtarzaj pytań już completed (✅)
- Jeśli odkrycia sugerują nowy wątek - użyj spawn_question
- Co kilka iteracji używaj update_knowledge
- Kończymy gdy: 80%+ pytań zbadanych LUB znaleźliśmy główne odpowiedzi
- Maksymalnie {state.plan.max_iterations} iteracji
</rules>

</task>

Co robisz TERAZ?"""




class ExecuteSearch(BaseModel):
    """Wykonaj wyszukiwanie dla konkretnego pytania"""
    action: Literal["execute_search"] = "execute_search"
    question_id: str = Field(..., description="ID pytania do zbadania")
    refined_query: Optional[str] = Field(None, description="Opcjonalnie ulepszone zapytanie")


class SpawnQuestion(BaseModel):
    """Wygeneruj nowe pytanie na podstawie odkryć"""
    action: Literal["spawn_question"] = "spawn_question"
    new_question: str = Field(..., description="Nowe pytanie badawcze")
    search_query: str = Field(..., description="Zapytanie do wyszukiwarki")
    dimension: str = Field(..., description="Wymiar, do którego należy")
    source_type: Literal["academic", "developer", "community", "official", "news", "general"]
    rationale: str = Field(..., description="Dlaczego to pytanie jest ważne")
    parent_question_id: str = Field(..., description="ID pytania źródłowego")

class UpdateKnowledge(BaseModel):
    """Zaktualizuj stan wiedzy na podstawie znalezisk"""
    action: Literal["update_knowledge"] = "update_knowledge"
    new_facts: List[str] = Field(default_factory=list)
    new_hypotheses: List[str] = Field(default_factory=list)
    new_contradictions: List[str] = Field(default_factory=list)
    new_gaps: List[str] = Field(default_factory=list)
    new_entities: List[str] = Field(default_factory=list)

class RecalibratePlan(BaseModel):
    """Przekalibruj plan badawczy"""
    action: Literal["recalibrate_plan"] = "recalibrate_plan"
    questions_to_deprioritize: List[str] = Field(default_factory=list, description="IDs pytań do obniżenia priorytetu")
    questions_to_prioritize: List[str] = Field(default_factory=list, description="IDs pytań do podwyższenia priorytetu")
    rationale: str = Field(..., description="Uzasadnienie rekalibracji")


class ConcludeResearch(BaseModel):
    """Zakończ research i przejdź do syntezy"""
    action: Literal["conclude"] = "conclude"
    summary: str = Field(..., description="Krótkie podsumowanie dlaczego kończymy")
    coverage_assessment: Literal["comprehensive", "adequate", "partial", "insufficient"]
    remaining_gaps: List[str] = Field(default_factory=list)



# ═══════════════════════════════════════════════════════════════════════════════
#                      SCHEMA-GUIDED REASONING - NextStep
# ═══════════════════════════════════════════════════════════════════════════════

class NextStep(BaseModel):
    """
    Główna struktura SGR - model musi przejść przez rozumowanie
    przed podjęciem decyzji o następnym kroku.
    """
    
    # === FAZA 1: Analiza obecnego stanu ===
    situation_analysis: str = Field(
        ...,
        description="Analiza obecnej sytuacji: co wiemy, czego szukamy, jakie mamy luki"
    )
    
    # === FAZA 2: Ocena postępu ===
    progress_assessment: str = Field(
        ...,
        description="Ocena postępu: ile pytań zbadano, jakie wymiary pokryto"
    )
    
    # === FAZA 3: Identyfikacja priorytetów ===
    current_priorities: Annotated[List[str], MinLen(1), MaxLen(3)] = Field(
        ...,
        description="Top 1-3 rzeczy do zrobienia teraz"
    )
    
    # === FAZA 4: Decyzja o działaniu ===
    should_continue: bool = Field(
        ...,
        description="Czy kontynuować research, czy mamy wystarczająco danych"
    )
    
    # === FAZA 5: Wybór akcji ===
    next_action: Union[
        ExecuteSearch,
        SpawnQuestion, 
        UpdateKnowledge,
        RecalibratePlan,
        ConcludeResearch
    ] = Field(..., discriminator="action")



def run_sgr_step(state: ResearchState) -> NextStep:
    """
    Wykonuje jeden krok SGR - model decyduje co dalej.
    """

    system_prompt = build_sgr_prompt(state)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Przeanalizuj sytuację i podejmij decyzję o następnym kroku."}
    ]


    return h.call_api(messages, NextStep)

    
    
    
    
# ═══════════════════════════════════════════════════════════════════════════════
#                      DISPATCHER - WYKONANIE AKCJI
# ═══════════════════════════════════════════════════════════════════════════════

def dispatch_action(action, state: ResearchState) -> str:
    """
    Wykonuje akcję zdecydowaną przez SGR.
    Zwraca feedback dla następnej iteracji.
    """

    if isinstance(action, ExecuteSearch):
        # Znajdź pytanie
        question = None
        for q in state.plan.questions:
            if q.id == action.question_id:
                question = q
                break

        if not question:
            return f"❌ Pytanie {action.question_id} nie znalezione"

        if question.status == "completed":
            return f"⚠️ Pytanie {action.question_id} już zostało zbadane"

        # Wykonaj wyszukiwanie
        findings = execute_search(question, action.refined_query)

        # Zapisz wyniki
        state.findings.extend(findings)
        state.mark_question_completed(action.question_id)

        return f"✅ Znaleziono {len(findings)} wyników dla [{action.question_id}]"

    elif isinstance(action, SpawnQuestion):
        # Generuj nowe ID
        existing_ids = [q.id for q in state.plan.questions]
        new_id = f"Q{len(existing_ids) + 1}"

        new_question = SubQuestion(
            id=new_id,
            question=action.new_question,
            search_query=action.search_query,
            dimension=action.dimension,
            source_type=action.source_type,
            status="pending",
            parent_question_id=action.parent_question_id
        )

        state.add_question(new_question)

        return f"🆕 Dodano nowe pytanie [{new_id}]: {action.new_question[:50]}..."

    elif isinstance(action, UpdateKnowledge):
        state.knowledge.confirmed_facts.extend(action.new_facts)
        state.knowledge.hypotheses.extend(action.new_hypotheses)
        state.knowledge.contradictions.extend(action.new_contradictions)
        state.knowledge.knowledge_gaps.extend(action.new_gaps)
        state.knowledge.key_entities.extend(action.new_entities)

        return f"📚 Zaktualizowano wiedzę: +{len(action.new_facts)} faktów, +{len(action.new_gaps)} luk"

    elif isinstance(action, RecalibratePlan):
        # W uproszczonej wersji tylko logujemy
        return f"🔄 Plan przekalibrowany: {action.rationale[:50]}..."

    elif isinstance(action, ConcludeResearch):
        return f"🏁 ZAKOŃCZENIE: {action.summary}"

    return "❓ Nieznana akcja"

    
# ═══════════════════════════════════════════════════════════════════════════════
#                      SYNTEZA KOŃCOWA
# ═══════════════════════════════════════════════════════════════════════════════

def synthesize_final_report(state: ResearchState) -> FinalReport:
    """
    Syntezuje wszystkie odkrycia w końcowy raport.
    """
    
    # Przygotuj kontekst źródeł
    sources_context = "\n".join([
        f"[{i+1}] {f.source_title}\n    URL: {f.source_url}\n    Treść: {f.content[:300]}..."
        for i, f in enumerate(state.findings[:20])  # Limit dla kontekstu
    ])
    
    knowledge_context = f"""
POTWIERDZONE FAKTY:
<confirmed_facts>
{chr(10).join('- ' + f for f in state.knowledge.confirmed_facts[:10])}
</confirmed_facts>

ZIDENTYFIKOWANE LUKI:
<knowledge_gaps>
{chr(10).join('- ' + g for g in state.knowledge.knowledge_gaps[:5])}
</knowledge_gaps>

SPRZECZNOŚCI:
<contradictions>
{chr(10).join('- ' + c for c in state.knowledge.contradictions[:5])}
</contradictions>
"""
    
    system_prompt = f"""Jesteś ekspertem od syntezy badań. 

Przygotuj KOMPLETNY RAPORT BADAWCZY na podstawie zebranych danych.

ZAPYTANIE UŻYTKOWNIKA: "{state.user_query}"

═══════════════════════════════════════════════════════════════════════════════
ZEBRANE ŹRÓDŁA (cytuj używając [nr]):
═══════════════════════════════════════════════════════════════════════════════
<sources_context>
{sources_context}
</sources_context>

═══════════════════════════════════════════════════════════════════════════════
STAN WIEDZY:
═══════════════════════════════════════════════════════════════════════════════
<knowledge_context>
{knowledge_context}
</knowledge_context>

═══════════════════════════════════════════════════════════════════════════════
WYMAGANIA RAPORTU:
═══════════════════════════════════════════════════════════════════════════════
<requirements>
1. executive_summary: 3-5 zdań odpowiadających BEZPOŚREDNIO na pytanie użytkownika
2. key_findings: 5-8 kluczowych odkryć jako bullet points (każdy z [numerem cytowania])
3. detailed_sections: 2-4 sekcje tematyczne z pogłębioną analizą
4. knowledge_gaps: co jeszcze warto zbadać
5. contradictions_and_debates: jeśli źródła się nie zgadzają
6. sources: lista cytowanych źródeł z oceną relevance
7. confidence_level: high/medium/low na podstawie jakości i zgodności źródeł
</requirements>

ZASADY:
<rules>
- KAŻDE twierdzenie musi mieć cytowanie [nr]
- Nie hallucynuj - używaj TYLKO dostarczonych źródeł
- Bądź konkretny i merytoryczny
- Jeśli źródła są sprzeczne - zaznacz to
</rules>
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Wygeneruj kompletny raport badawczy."}
    ]
    

    report = h.call_api(messages, FinalReport)
    
    # Dodaj metadane
    report.research_metadata = {
        "query": state.user_query,
        "total_iterations": state.iteration,
        "questions_explored": len(state.get_completed_questions()),
        "total_findings": len(state.findings),
        "timestamp": datetime.now().isoformat()
    }
    
    return report

#=========================================================================================        

def execute_search(question: SubQuestion, refined_query: Optional[str] = None) -> List[Finding]:
    """
    Wykonuje wyszukiwanie dla konkretnego pytania badawczego.
    Zwraca listę Finding objects.
    """

    query = refined_query or question.search_query

    # Dobierz domenę na podstawie source_type
    search_params = {
        "query": query,
        "max_results": 5,
    }

    if question.source_type != "general":
        domains = DOMAIN_PRESETS.get(question.source_type, [])
        if domains:
            search_params["include_domains"] = domains

    if question.source_type == "news":
        search_params["topic"] = "news"
        search_params["time_range"] = "month"

    try:
        response = tavily_client.search(**search_params)
        results = response.get("results", [])
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        return []

    findings = []
    for r in results:
        finding = Finding(
            content=r.get("content", "")[:500],  # Truncate
            source_url=r.get("url", ""),
            source_title=r.get("title", "Unknown"),
            relevance_score=r.get("score", 0.5),
            question_id=question.id,
            finding_type="fact"  # Simplified - could be enhanced with classification
        )
        findings.append(finding)

    return findings

def deep_research(user_query: str, max_iterations: int = 10) -> FinalReport:
    """
    Główna funkcja - przeprowadza głęboki research z adaptywnym planowaniem.
    """

    console.print(Panel(
        f"[bold]{user_query}[/bold]",
        title="🔬 DEEP RESEARCH INITIATED",
        border_style="cyan"
    ))

    # === Dekompozycja strategiczna ===
    console.print("\n")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🧠 Strategiczna dekompozycja zapytania...", total=None)
        plan = decompose_query(user_query)
        progress.remove_task(task)

    console.print(f"✅ Plan utworzony: {len(plan.dimensions)} wymiarów, {len(plan.questions)} pytań")
    console.print(f"   Głębokość: [cyan]{plan.estimated_depth}[/cyan]")

    # Wyświetl plan
    tree = Tree("📋 Plan Badawczy")
    for dim in plan.dimensions:
        dim_branch = tree.add(f"[bold]{dim.name}[/bold] ({dim.priority})")
        for q in plan.questions:
            if q.dimension == dim.name:
                dim_branch.add(f"[{q.id}] {q.question[:50]}... ({q.source_type})")
    console.print(tree)

    # === Inicjalizacja stanu ===
    plan.max_iterations = max_iterations
    state = ResearchState(plan, user_query)
    state.log_plan_state()

    # === Adaptacyjna pętla badawcza ===
    console.print("\n")
    console.print(Rule("🔄 ADAPTIVE RESEARCH LOOP"))

    for i in range(max_iterations):
        state.iteration = i + 1

        console.print(f"\n[bold cyan]═══ ITERACJA {i+1}/{max_iterations} ═══[/bold cyan]")

        # SGR Decision
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤔 SGR reasoning...", total=None)
            step = run_sgr_step(state)
            progress.remove_task(task)

        # Wyświetl reasoning
        console.print(f"\n[dim]Analiza: {step.situation_analysis[:100]}...[/dim]")
        console.print(f"[dim]Priorytety: {', '.join(step.current_priorities)}[/dim]")
        console.print(f"Kontynuować: {'✅ TAK' if step.should_continue else '🏁 NIE'}")

        # Sprawdź czy kończymy
        if isinstance(step.next_action, ConcludeResearch):
            console.print(f"\n[green]🏁 ZAKOŃCZENIE: {step.next_action.summary}[/green]")
            break

        # Wykonaj akcję
        action_name = step.next_action.action
        console.print(f"\n⚡ Akcja: [yellow]{action_name}[/yellow]")

        feedback = dispatch_action(step.next_action, state)
        console.print(f"   {feedback}")

        # Zapisz stan
        state.log_plan_state()
        state.action_log.append(f"[{i+1}] {action_name}: {feedback}")

    # === Podsumowanie ewolucji ===
    console.print("\n")
    display_plan_evolution(state)

    # ===  Synteza końcowa ===
    console.print("\n")
    console.print(Rule("📊 SYNTHESIS PHASE"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("✍️ Generating final report...", total=None)
        report = synthesize_final_report(state)
        progress.remove_task(task)

    # === Prezentacja raportu ===
    display_report(report)

    return report



def display_plan_evolution(state: ResearchState):
    """Wyświetla ewolucję planu w czasie"""

    if len(state.plan_history) < 2:
        return

    table = Table(title="📈 Ewolucja Planu Badawczego")
    table.add_column("Iteracja", style="cyan")
    table.add_column("Pending", style="yellow")
    table.add_column("Done", style="green")
    table.add_column("Findings", style="blue")
    table.add_column("Facts", style="magenta")
    table.add_column("Gaps", style="red")

    for snap in state.plan_history:
        table.add_row(
            str(snap["iteration"]),
            str(snap["pending_count"]),
            str(snap["completed_count"]),
            str(snap["total_findings"]),
            str(snap["knowledge_facts"]),
            str(snap["knowledge_gaps"])
        )

    console.print(table)


def display_report(report: FinalReport):
    """Wyświetla raport w czytelnej formie"""

    console.print("\n")
    console.print(Panel(
        report.executive_summary,
        title="📋 EXECUTIVE SUMMARY",
        border_style="green"
    ))

    console.print("\n")
    console.print(Rule("🔑 KEY FINDINGS"))
    for i, finding in enumerate(report.key_findings, 1):
        console.print(f"  {i}. {finding}")

    console.print("\n")
    for section in report.detailed_sections:
        console.print(Panel(
            section.content,
            title=f"📖 {section.title}",
            border_style="blue"
        ))

    if report.knowledge_gaps:
        console.print("\n")
        console.print(Rule("❓ KNOWLEDGE GAPS"))
        for gap in report.knowledge_gaps:
            console.print(f"  • {gap}")

    if report.contradictions_and_debates:
        console.print("\n")
        console.print(Rule("⚔️ CONTRADICTIONS & DEBATES"))
        for c in report.contradictions_and_debates:
            console.print(f"  • {c}")

    console.print("\n")
    console.print(Rule("📚 SOURCES"))
    for src in report.sources:
        console.print(f"  [{src.id}] {src.title}")
        console.print(f"      {src.url}")
        console.print(f"      [dim]{src.relevance}[/dim]")

    console.print("\n")
    confidence_color = {"high": "green", "medium": "yellow", "low": "red"}[report.confidence_level]
    console.print(f"Confidence: [{confidence_color}]{report.confidence_level.upper()}[/{confidence_color}]")
    console.print(f"[dim]Metadane: {json.dumps(report.research_metadata, indent=2)}[/dim]")
    
    


DEMO_QUERIES = [
    # Techniczne deep-dive
    "What are the current state-of-the-art architectures for AI agents in production systems?",

    # Porównawcze
    "Compare RAG vs Fine-tuning for enterprise LLM applications: when to use which?",

    # Trendy i przyszłość
    "What are the emerging trends in AI safety and alignment research in 2024-2025?",

    # Praktyczne
    "Best practices for building reliable multi-agent systems with tool use",

    # Kontrowersyjne/debatowe
    "Is AGI approaching? What do researchers and industry experts disagree about?",
]


def run_deep_research(query=None):

    console.print(Panel(
        "[bold]Deep Research Assistant z adaptywnym planowaniem[/bold]\n\n"
        "System wykorzystuje Schema-Guided Reasoning do prowadzenia\n"
        "wielowymiarowego researchu z dynamiczną kalibracją planu.",
        title="🔬 Demo",
        border_style="cyan"
    ))


    # Wybierz zapytanie
    if query is None:
        console.print("\n[bold]Dostępne zapytania demo:[/bold]")
        for i, q in enumerate(DEMO_QUERIES, 1):
            console.print(f"  {i}. {q[:70]}...")

        console.print(f"\n  0. [Własne zapytanie]")
        choice = console.input("\n[bold]Wybierz (1-5) lub 0 dla własnego: [/bold]")

        if choice == "0":
            query = console.input("[bold]Wpisz swoje zapytanie: [/bold]")
        else:
            try:
                query = DEMO_QUERIES[int(choice) - 1]
            except (ValueError, IndexError):
                query = DEMO_QUERIES[0]
    
    
    # Uruchom research
    report = deep_research(query, max_iterations=8)

    console.print("\n\n")
    console.print(Panel(
        "Research zakończony! Raport został wygenerowany powyżej.",
        title="✅ COMPLETE",
        border_style="green"
    ))

if __name__ == "__main__":  
    run_deep_research("What are the current state-of-the-art architectures for AI agents in production systems?")    
