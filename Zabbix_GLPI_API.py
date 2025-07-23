#!/usr/bin/env python3

# Dodatkwe ustawienia od strony zabbixa:
# 1. Dodanie "Media Type" o typie script i wpisanie dokładnie nazwy skryptu z maszyny. Dodanie w dwóch odzielnych polach zmiennych {ALERT.SUBJECT} {ALERT.MESSAGE}, po czym upewnienie się że enabled.
# 2. Kolejnym krokiem jest przypisanie, utworzonego w poprzednim punkcie Media Type któremuś z użytkowników (np. Admin), wybranie docelowych poziomów powiadamiania oraz kiedy powiadamianie ma występować, oraz "byle jakie" wypełnienie pola "Send to"
#    gdyż skrypt tego nie używa. Upewnienie się że enabled.
# 3. Przejście do Action->trigger action, dodanie nowej akcji oraz jej nazwanie. Typ obliczania: "AND" lub "AND/OR", dodanie dwóch warunków "trigger severity equals high" oraz "trigger severity equals disaster". 
#    Następnie w operacjach zmienić czas na 60s (minimalny), kliknąć Add w Operations; Steps: 1-1; Step duraiton:0; Send to group:zostawiamy; Send to users:<Wybieramy użtkownika, który został wybrany w punkcie drugim>;
#    Send only to:<nazwa media type>; i Custom message wygląda jak poniżej:
#                                                                  Subcjet: Problem: {HOST.NAME} ({HOST.IP})
#                                                                  Message: Problem: {EVENT.NAME}
#                                                                           Priorytet: {TRIGGER.SEVERITY}
#                                                                           Trigger: {TRIGGER.NAME}
#                                                                           Opis wyzwalacza: 
#                                                                           {TRIGGER.DESCRIPTION}
#                                                                           Data: {EVENT.DATE} 
#                                                                           Godzina: {EVENT.TIME}
#                                                                           ID zdarzenia: {EVENT.ID}
#    
#    Zaznaczamy "Paused operations for suppressed problems" oraz "Notify about canceled excalations"
#
# 4. I teraz test i powinno być git.

import subprocess
import json
import sys
import os

# GLPI API Configuration
GLPI_URL = "https://pathto.glpi/apirest.php/" # URL to GLPI
GLPI_APP_TOKEN = "API" # GLPI API Token
GLPI_USER_TOKEN = "API" # User API Token from GLPI

if len(sys.argv) < 3:
    print("Usage: zabbix_glpi_ticket.py <subject> <message>", file=sys.stderr)
    sys.exit(1)


subject = sys.argv[1]
message = sys.argv[2]

session_token=None

try:
    print("Próba inicjalizacji sesji GLPI za pomocą curl...", file=sys.stderr)
    curl_init_cmd=[
            "curl", "-k", "-s", "-L", "-X", "GET",
            "-H", "Content-Type: application/json",
            "-H", f"App-Token: {GLPI_APP_TOKEN}",
            "-H", f"Authorization: user_token {GLPI_USER_TOKEN}",
            f"{GLPI_URL}initSession"
            ]
    init_session_result = subprocess.run(curl_init_cmd, capture_output=True, text=True, check=False)

    if init_session_result.returncode != 0:
        print(f"Błąd curl podczas inicjalizacji sesji: {init_session_result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Surowa odpowiedź initSession (stdout): '{init_session_result.stdout}'", file=sys.stderr)
    print(f"Surowa odpowiedź initSession (stderr): '{init_session_result.stderr}'", file=sys.stderr)

    try:
        session_data = json.loads(init_session_result.stdout)
        if isinstance(session_data, list) and len(session_data) > 0 and isinstance(session_data[0], dict):
            session_token = session_data[0].get('session_token')
        elif isinstance(session_data, dict):
            session_token = session_data.get('session_token')
        else:
            raise json.JSONDecodeError(f"Nieoczekiwany format danych sesji: {type(session_data)}", init_session_result.stdout, 0)
    except json.JSONDecodeError as e:
        print(f"Błąd dekodowania JSON odpowiedzi initSession: {e}", file=sys.stderr)
        print(f"Surowa odpowiedź initSession: {init_session_result.stdout}", file=sys.stderr)
        sys.exit(1)


    if not session_token:
        print(f"Błąd: Nie można uzyskać tokena sesji z GLPI. Odpowiedź: {init_session_result.stdout}", file=sys.stderr)
        sys.exit(1)

    print(f"Sesja GLPI zainicjalizowana. Token sesji: {session_token}", file=sys.stderr)

    ticket_payload={
            "input": {
                "name": subject,
                "content": message,
                "urgency": 3,
                "impact": 3,
                "type": 1,
                }
            }
    ticket_payload_json = json.dumps(ticket_payload)
    print(f"Ładunek zgłoszenia: {ticket_payload_json}", file=sys.stderr)

    print("Próba utworzenia zgłoszenia GLPI za pomocą curl...", file=sys.stderr)
    curl_create_ticket_cmd = [
            "curl", "-k", "-L", "-s",  "-X", "POST",
            "-H", "Content-Type: application/json",
            "-H", f"App-Token: {GLPI_APP_TOKEN}",
            "-H", f"Session-Token: {session_token}",
            "-d", ticket_payload_json,
            f"{GLPI_URL}Ticket"
            ]
    create_ticket_result = subprocess.run(curl_create_ticket_cmd, capture_output=True, text=True, check=False)

    if create_ticket_result.returncode != 0:
        print(f"Błąd curl podczas tworzenia zgłoszenia: {create_ticket_result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        ticket_response_data = json.loads(create_ticket_result.stdout)
        if isinstance(ticket_response_data, dict) and 'id' in ticket_response_data:
            ticket_id = ticket_response_data['id']
            print(f"Pomyślnie utworzono zgłoszenie GLPI o ID: {ticket_id}. Odpowiedź API GLPI: {ticket_response_data}", file=sys.stderr)
        else:
            print(f"Pomyślnie utworzono zgłoszenie GLPI. Nieoczekiwany format odpowiedzi API GLPI: {ticket_response_data}", file=sys.stderr)
            print("OSTRZEŻENIE: GLPI zwróciło nieoczekiwany format odpowiedzi dla pomyślnego POST do utworzenia nowego zgłoszenia. Sprawdź logi serwera GLPI.", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"Błąd dekodowania JSON odpowiedzi tworzenia zgłoszenia: {e}", file=sys.stderr)
        print(f"Surowa odpowiedź tworzenia zgłoszenia: {create_ticket_result.stdout}", file=sys.stderr)
        sys.exit(1)

except Exception as e:
    print(f"Wystąpił nieoczekiwany błąd: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if session_token:
        print("Próba zakończenia sesji GLPI za pomocą curl...", file=sys.stderr)
        curl_kill_session_cmd = [
                "curl", "-k", "-L", "-s", "-X", "GET",
                "-H", "Content-Type: application/json",
                "-H", f"App-Token: {GLPI_APP_TOKEN}",
                "-H", f"Session-Token: {session_token}",
                f"{GLPI_URL}killSession"
                ]
        kill_session_result = subprocess.run(curl_kill_session_cmd, capture_output=True, text=True, check=False)
        if kill_session_result.returncode == 0:
            print("Sesja GLPI pomyślnie zakończona.", file=sys.stderr)
        else:
            print(f"Ostrzeżenie: Nie można zakończyć sesji GLPI. Błąd curl: {kill_session_result.stderr}", file=sys.stderr)