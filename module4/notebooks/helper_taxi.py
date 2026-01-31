

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
import helper as h

class TaxiScenario(str, Enum):
    """Scenariusze symulacji taksówki"""
    HAPPY_PATH = "HAPPY_PATH"
    NO_CARS_AVAILABLE = "NO_CARS_AVAILABLE"
    LONG_WAIT_TIME = "LONG_WAIT_TIME"
    SPECIAL_REQUEST_UNAVAILABLE = "SPECIAL_REQUEST_UNAVAILABLE"
    ADDRESS_AMBIGUOUS = "ADDRESS_AMBIGUOUS"
    DRIVER_CANCELLED = "DRIVER_CANCELLED"
    DRIVER_DELAYED = "DRIVER_DELAYED"
    DRIVER_CANT_FIND = "DRIVER_CANT_FIND"
    PRICE_TOO_HIGH = "PRICE_TOO_HIGH"

class TaxiResponse(BaseModel):
    """Odpowiedź dyspozytora"""
    response: str = Field(description="Co dyspozytor mówi do agenta")
    booking_id: Optional[str] = Field(None, description="ID zamówienia jeśli zostało utworzone")
    driver_assigned: bool = Field(False, description="Czy kierowca został przydzielony?")

def simulate_taxi_dispatcher(agent_says: str, goal, state) -> str:
    """Symuluje dyspozytora taksówki"""
    
    scenario = getattr(goal, 'scenario', TaxiScenario.HAPPY_PATH)
    
    # Scenariusze
    scenario_prompts = {
        TaxiScenario.HAPPY_PATH: f"""
SCENARIUSZ: HAPPY PATH
- Przyjmij zamówienie normalnie
- Jeśli agent wspomina o foteliku/dużym bagażniku → potwierdź dostępność
- Gdy agent poda nazwisko → przydziel kierowcę (Skoda Octavia, WX 12345, kierowca Piotr)
- Czas oczekiwania: 8 minut
- Cena: około 80 zł
""",
        TaxiScenario.NO_CARS_AVAILABLE: """
SCENARIUSZ: BRAK SAMOCHODÓW
- Przeproś - wszystkie samochody zajęte
""",
        TaxiScenario.LONG_WAIT_TIME: """
SCENARIUSZ: DŁUGI CZAS OCZEKIWANIA
- Czas oczekiwania: 25 minut
""",
        TaxiScenario.SPECIAL_REQUEST_UNAVAILABLE: """
SCENARIUSZ: BRAK WYPOSAŻENIA SPECJALNEGO
- Jeśli agent prosi o fotelik → odmów (brak dostępności)
""",
        TaxiScenario.PRICE_TOO_HIGH: f"""
SCENARIUSZ: CENA ZA WYSOKA
- Szacowana cena: 180 PLN
"""
    }
    
    scenario_instruction = scenario_prompts.get(scenario, scenario_prompts[TaxiScenario.HAPPY_PATH])
    
    # Kontekst stanu - używamy nowych nazw pól
    addresses_validated = getattr(state, 'addresses_validated', set())
    price_quoted = getattr(state, 'price_quoted', None)
    special_confirmed = getattr(state, 'special_confirmed', False)
    name_given = getattr(state, 'name_given', False)
    
    state_context = f"""
OBECNY STAN ROZMOWY:
- Booking ID: {state.booking_id or 'nie utworzono'}
- Kierowca przydzielony: {state.driver_assigned}
- Adresy zwalidowane: {len(addresses_validated)} 
- Cena podana: {price_quoted or 'nie'}
- Wymagania specjalne potwierdzone: {special_confirmed}
- Nazwisko podane: {name_given}
"""

    prompt = f"""Jesteś dyspozytorem w korporacji taksówkarskiej odbierającym telefon od agenta.

{scenario_instruction}

{state_context}

KONTEKST ZAMÓWIENIA:
- Z: {goal.pickup_address}
- Do: {goal.destination}
- Czas: {goal.time_preference}
- Pasażerów: {goal.passenger_count}

AGENT MÓWI:
"{agent_says}"

ZASADY:
- Odpowiedź max 2-3 zdania
- Bądź profesjonalny i uprzejmy
- Jeśli agent pyta o cenę → podaj cenę
- Jeśli agent pyta o fotelik/bagażnik → potwierdź lub odmów (zależy od scenariusza)
- Jeśli agent podaje nazwisko → przydziel kierowcę

TWOJA ODPOWIEDŹ:"""

    messages = [{"role": "user", "content": prompt}]
    result = h.call_api(messages, response_model=TaxiResponse)
    
    # Aktualizuj stan
    if result.booking_id and not state.booking_id:
        state.booking_id = result.booking_id
        state.driver_status_db[result.booking_id] = {
            "status": "assigned",
            "eta_minutes": 8,
            "driver": "Piotr",
            "car": "Skoda Octavia WX 12345"
        }
    
    if result.driver_assigned:
        state.driver_assigned = True
    
    return result.response
