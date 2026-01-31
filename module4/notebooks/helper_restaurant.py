from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
import helper as h
    

class ReservationGoal(BaseModel):
    """Cel rezerwacji"""
    restaurant: str
    date: str
    time: str
    party_size: int
    flexibility_min: int = 30

        
class RestaurantScenario(str, Enum):
    """Scenariusze symulacji restauracji"""
    HAPPY_PATH = "happy_path"              # Wszystko OK, rezerwacja potwierdzona
    FULLY_BOOKED = "fully_booked"          # Zajęte, brak alternatywy
    ALTERNATIVE_TIME = "alternative_time"   # Zajęte, proponuje ±30 min
    REQUIRE_PREPAYMENT = "require_prepayment" # OK ale wymaga przedpłaty
    ALLERGY_PROBLEM = "allergy_problem"    # Nie mogą zagwarantować braku alergenu
    MIN_PARTY_SIZE = "min_party_size"      # Tylko dla 4+ osób
    
class RestaurantResponse(BaseModel):
    """Odpowiedź restauracji"""
    response: str = Field(description="Co restauracja mówi do agenta")
    is_confirmed: bool = Field(description="Czy rezerwacja POTWIERDZONA (zapisana w systemie)?")
        
      
        
def simulate_restaurant(
    agent_says: str, 
    scenario: RestaurantScenario = RestaurantScenario.HAPPY_PATH,
    goal: Optional[ReservationGoal] = None  # Żeby wiedzieć o czym mowa
) -> str:
    """
    Symuluje restaurację z różnymi scenariuszami.
    
    Args:
        agent_says: Co agent powiedział
        scenario: Jaki scenariusz symulować
        goal: Cel rezerwacji (potrzebny dla kontekstu)
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIUSZE - różne instrukcje dla LLM
    # ═══════════════════════════════════════════════════════════════════════
    
    scenario_prompts = {
        RestaurantScenario.HAPPY_PATH: """
SCENARIUSZ: HAPPY PATH
- Przyjmij rezerwację normalnie
- Gdy dostaniesz nazwisko + datę + godzinę + liczbę osób → potwierdź
- Format potwierdzenia: "Doskonale! Zapisałem rezerwację na nazwisko [X]. Do zobaczenia!"
""",
        
        RestaurantScenario.FULLY_BOOKED: """
SCENARIUSZ: RESTAURACJA PEŁNA
- Przeproś - restauracja całkowicie zarezerwowana tego dnia
- Zaproponuj inny dzień (następny lub poprzedni)
- Bądź uprzejmy ale stanowczy
- Przykład: "Niestety, ten dzień jest już całkowicie zarezerwowany. Mogę zaproponować [data-1] lub [data+1]?"
""",
        
        RestaurantScenario.ALTERNATIVE_TIME: f"""
SCENARIUSZ: ALTERNATYWNA GODZINA
- Podana godzina zajęta
- Zaproponuj ±30 minut (np. jeśli prosi o 19:00 → zaproponuj 18:30 lub 19:30)
- Jeśli agent zaakceptuje nową godzinę → potwierdź rezerwację
- Przykład: "O {goal.time if goal else '19:00'} już nie mamy wolnych stolików. Mogę zaproponować {_adjust_time(goal.time if goal else '19:00', -30)} lub {_adjust_time(goal.time if goal else '19:00', 30)}?"
""",
        
        RestaurantScenario.REQUIRE_PREPAYMENT: """
SCENARIUSZ: WYMÓG PRZEDPŁATY
- Rezerwacja możliwa ale wymaga przedpłaty 50 zł
- Zapytaj o zgodę na przedpłatę
- Jeśli agent się zgodzi → daj numer konta lub link
- Potem potwierdź rezerwację
- Przykład: "Możemy zarezerwować, ale wymagamy przedpłaty 50 zł. Czy to OK?"
""",
        
        RestaurantScenario.ALLERGY_PROBLEM: """
SCENARIUSZ: PROBLEM Z ALERGIĄ
- Jeśli agent wspomni o alergii na orzechy → przeproś, nie możecie zagwarantować
- Kuchnia używa orzechów w wielu daniach, ryzyko cross-contamination
- Zaproponuj inne restauracje lub odmów rezerwacji
- Przykład: "Niestety, nie możemy zagwarantować całkowitego braku orzechów w daniach. Dla bezpieczeństwa klienta radzimy wybrać inną restaurację."
""",
        
        RestaurantScenario.MIN_PARTY_SIZE: """
SCENARIUSZ: MINIMALNA LICZBA OSÓB
- Akceptujemy tylko rezerwacje dla 4+ osób
- Jeśli agent rezerwuje dla 1-3 osób → grzecznie odmów
- Zaproponuj przyjście bez rezerwacji (miejsca przy barze)
- Przykład: "Rezerwacje przyjmujemy od 4 osób wzwyż. Dla mniejszych grup zapraszamy bez rezerwacji - mamy miejsca przy barze!"
"""
    }
    
    scenario_instruction = scenario_prompts.get(scenario, scenario_prompts[RestaurantScenario.HAPPY_PATH])
    
    # ═══════════════════════════════════════════════════════════════════════
    # GŁÓWNY PROMPT
    # ═══════════════════════════════════════════════════════════════════════
    
    prompt = f"""Jesteś pracownikiem restauracji odbierającym telefon od agenta rezerwacji.

{scenario_instruction}

KONTEKST REZERWACJI (jeśli znany):
- Restauracja: {goal.restaurant if goal else 'nieznana'}
- Data: {goal.date if goal else 'nieznana'}
- Godzina: {goal.time if goal else 'nieznana'}
- Liczba osób: {goal.party_size if goal else 'nieznana'}

AGENT MÓWI:
"{agent_says}"

ZASADY OGÓLNE:
- Odpowiedź max 2-3 zdania
- Bądź uprzejmy i profesjonalny
- Jeśli agent pyta o coś poza scenariuszem → improwizuj realistycznie

TWOJA ODPOWIEDŹ:"""

    # ═══════════════════════════════════════════════════════════════════════
    # WYWOŁANIE LLM
    # ═══════════════════════════════════════════════════════════════════════
    
    messages = [{"role": "user", "content": prompt}]
    
    result = h.call_api(messages, response_model=RestaurantResponse)
    
    return result.response



# ═══════════════════════════════════════════════════════════════════════════
# HELPER: Dodaj/odejmij minuty od godziny
# ═══════════════════════════════════════════════════════════════════════════

def _adjust_time(time_str: str, minutes: int) -> str:
    """
    Zmienia godzinę o podaną liczbę minut.
    
    Examples:
        _adjust_time("19:00", 30) -> "19:30"
        _adjust_time("19:00", -30) -> "18:30"
    """    
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        new_dt = dt + timedelta(minutes=minutes)
        return new_dt.strftime("%H:%M")
    except:
        return time_str  # Jeśli parsing nie działa, zwróć original
