from enum import Enum
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()


client = instructor.patch(
    OpenAI(base_url = "https://llm-api.dataworkshop.eu"), 
    mode=instructor.Mode.MD_JSON
)


def call_api(messages, response_model, model="gemini-3-pro-preview"):
    response = client.chat.completions.create(
        model=model,  
        messages=messages,
        response_model=response_model,
        temperature=0.0
    )
    
    return response



class BookingStatus(str, Enum):
    START = "START"
    INITIATION = "INITIATION"
    RESPONSE_ANALYSIS = "RESPONSE_ANALYSIS"
    AVAILABILITY_CONFIRMED = "AVAILABILITY_CONFIRMED"
    NEGOTIATION = "NEGOTIATION"
    COLLECTING_DATA = "COLLECTING_DATA"
    VERIFYING_CONDITION = "VERIFYING_CONDITION"
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
    RESERVATION_CONFIRMED = "RESERVATION_CONFIRMED"
    FAILED = "FAILED"
    END = "END"
    CORRECTION = "CORRECTION"
    CLARIFICATION = "CLARIFICATION"

    
    
booking_status_description = (
    "Critical evaluation of the booking process state after the last restaurant utterance. "
    "Use the FOLLOWING RULES to unequivocally select the most fitting state from the BookingStatus Enum:"
    "\n\n"
    "--- FINAL STATES ---"
    "\n"
    "1. `RESERVATION_CONFIRMED`: Use ONLY when the restaurant employee explicitly confirms the final booking "
    "(e.g., 'confirmed', 'booked', 'done') and all details are settled. This is the ultimate success state."
    "\n"
    "2. `FAILED`: Use when the restaurant definitively refuses the reservation with no alternatives "
    "(e.g., 'no tables available', 'we don't take reservations'). This is the ultimate failure state."
    "\n"
    "3. `END`: Use when the conversation is wrapping up with final pleasantries AFTER a `RESERVATION_CONFIRMED` or `FAILED` state has already been reached."
    "\n\n"
    "--- IN-PROGRESS & NEGOTIATION STATES ---"
    "\n"
    "4. `NEGOTIATION`: Use when the restaurant rejects the initial request BUT proposes an alternative "
    "(different time, date, party size, etc.)."
    "\n"
    "5. `COLLECTING_DATA`: Use when the main availability is confirmed and the restaurant is now asking "
    "for necessary details (e.g., 'What name should I put?', 'phone number?')."
    "\n\n"
    "--- WAITING & SPECIAL STATES ---"
    "\n"
    "6. `VERIFYING_CONDITION`: Use when the restaurant needs to check on a special request "
    "(e.g., 'Let me ask the chef about the gluten-free option'). The agent must wait."
    "\n"
    "7. `WAITING_FOR_PAYMENT`: Use when the restaurant requires an external action like a deposit payment."
    "\n"
    "8. `CLARIFICATION`: Use when there is a technical issue with communication "
    "(e.g., 'Sorry, could you repeat that?', 'the line is bad')."
    "\n\n"
    "--- INITIAL STATES ---"
    "\n"
    "9. `INITIATION`: Use only for the agent's very first turn when it starts the conversation."
)



class RestaurantResponseAnalysis(BaseModel):
    """
    Analyzes a single restaurant utterance, updates the state,
    and prepares the agent's next response.
    """
    analysis_summary: str = Field(
        ...,
        description="A brief, one-sentence summary in Polish of what the restaurant just said."
    )
    
    booking_status: BookingStatus = Field(
        ...,
        description=booking_status_description
    )
    
    ai_answer: str = Field(
        ...,
        description=(
            "Generate a precise, ready-to-speak response in Polish that is a logical continuation "
            "of the conversation to achieve the mission's goal."
        )
    )
        
        
#######################################################################################################################
#
#
#                         Taxi Dispatcher
#
#
######################################################################################################################
class TaxiBookingStatus(str, Enum):
    """Defines the possible states of the taxi booking process."""
    
    # Initial & Analysis states
    INITIATION = "INITIATION"
    RESPONSE_ANALYSIS = "RESPONSE_ANALYSIS"
    
    # Core logic & data collection states
    NEGOTIATION = "NEGOTIATION"
    COLLECTING_DETAILS = "COLLECTING_DETAILS"
    VERIFYING_SPECIAL_REQUEST = "VERIFYING_SPECIAL_REQUEST"
    
    # Confirmation & waiting states
    ORDER_CONFIRMED = "ORDER_CONFIRMED"
    AWAITING_DRIVER_ASSIGNMENT = "AWAITING_DRIVER_ASSIGNMENT"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    
    # Terminal states
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
    # Utility state
    CLARIFICATION = "CLARIFICATION"
    
    
    
taxi_status_description = """Krytyczna ocena stanu procesu rezerwacji po ostatniej wypowiedzi dyspozytora.
Użyj PONIŻSZYCH REGUŁ, aby jednoznacznie wybrać najbardziej pasujący stan z Enum-a TaxiBookingStatus:

--- STANY KOŃCOWE ---
1. `SUCCESS`: Użyj TYLKO wtedy, gdy dyspozytor jednoznacznie potwierdzi zamówienie ORAZ poda dane kierowcy/pojazdu. To ostateczny stan sukcesu.
2. `FAILED`: Użyj, gdy dyspozytor definitywnie odmawia przyjęcia zlecenia bez żadnych alternatyw (np. 'brak wolnych samochodów', 'nie obsługujemy tego rejonu').

--- STANY PROCESU ---
3. `NEGOTIATION`: Użyj, gdy dyspozytor informuje o czasie oczekiwania, który jest potencjalnie długi, lub proponuje alternatywę.
4. `COLLECTING_DETAILS`: Użyj, gdy główna dostępność jest potwierdzona, a dyspozytor prosi o dane (np. 'Na jakie nazwisko?', 'numer kontaktowy?').
5. `VERIFYING_SPECIAL_REQUEST`: Użyj, gdy dyspozytor musi sprawdzić dostępność pojazdu ze specjalnym wymaganiem (np. fotelik, kombi na bagaż).
6. `ORDER_CONFIRMED`: Użyj, gdy zlecenie zostało przyjęte, ale agent nie otrzymał jeszcze danych kierowcy.
7. `DRIVER_ASSIGNED`: Użyj, gdy dyspozytor przekazuje konkretne dane pojazdu i kierowcy.

--- STANY POCZĄTKOWE ---
8. `INITIATION`: Użyj tylko dla pierwszej tury agenta, gdy rozpoczyna rozmowę."""

class TaxiResponseAnalysis(BaseModel):
    analysis_summary: str = Field(
        ...,
        description="Krótkie, jednozdaniowe podsumowanie w języku polskim tego, co właśnie powiedział dyspozytor."
    )
    
    booking_status: TaxiBookingStatus = Field(
        ...,
        description=taxi_status_description
    )
    
    estimated_wait_time_minutes: Optional[int] = Field(
        None,
        description="Jeśli dyspozytor podał szacowany czas oczekiwania, wyodrębnij go i podaj jako liczbę całkowitą (minuty)."
    )
    
    ai_answer: str = Field(
        ...,
        description=(
            "Wygeneruj precyzyjną, gotową do wypowiedzenia odpowiedź w języku polskim, która jest logiczną kontynuacją "
            "rozmowy i dąży do realizacji celu misji."
        )
    )
