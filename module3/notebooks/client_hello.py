
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def run_client():
    # KROK 1: Konfiguracja parametrów serwera
    # Tutaj definiujemy, jak uruchomić nasz serwer.
    # W przypadku stdio, klient po prostu odpala skrypt serwera jako podproces.
    server_params = StdioServerParameters(
        command="python",           # Program do uruchomienia
        args=["server_hello.py"],   # Argumenty (nasz plik serwera)
        env=None                    # Zmienne środowiskowe (opcjonalne)
    )

    # stdio_client zarządza wejściem/wyjściem (stdin/stdout).
    # read = strumień danych OD serwera
    # write = strumień danych DO serwera
    async with stdio_client(server_params) as (read, write):
        
        # Uruchomienie sesji MCP (protocol layer)
        # ClientSession to "centrum dowodzenia", który zamienia surowe dane w obiekty MCP.
        async with ClientSession(read, write) as session:
            
            # Handshake - kluczowy moment!
            # Klient i Serwer wymieniają się informacjami o swoich możliwościach.
            await session.initialize()
            
            # --- TERAZ ZACZYNA SIĘ ZABAWA 🕺💃 ---
            
            # A. Odkrywanie narzędzi (Discovery)
            # Pytamy serwer: "Co potrafisz robić?"
            tools = await session.list_tools()
            print(f"Znalezione narzędzia: {[t.name for t in tools.tools]}")
            
            # B. Użycie narzędzia (Execution)
            # Mówimy: "Uruchom echo_tool z parametrem text='Hello World'"
            result = await session.call_tool(
                "echo_tool", 
                arguments={"text": "Hello World"}
            )
            # Serwer wykonuje kod i zwraca wynik
            print(f"Wynik narzędzia: {result.content[0].text}")

            # C. Czytanie zasobów 
            # Mówimy: "Pokaż mi zawartość pod adresem greeting://hello"
            resource = await session.read_resource("greeting://hello")
            print(f"Treść zasobu: {resource.contents[0].text}")

# Punkt wejścia programu 
if __name__ == "__main__":
    asyncio.run(run_client())
