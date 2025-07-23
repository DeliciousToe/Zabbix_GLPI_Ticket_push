# Zabbix GLPI Ticket Creation Script

This Python script (`curl_zabbix_glpi_ticket.py`) acts as a Zabbix Media Type script to automatically create tickets in GLPI for specific Zabbix alerts (e.g., High or Disaster severity). It leverages `curl` commands internally for robust communication with the GLPI REST API.

## Features

* Initiates a session with the GLPI API using App and User tokens.
* Creates a new GLPI ticket with a customizable subject and message.
* Sets urgency, impact, and type for the new ticket.
* Gracefully handles session termination.
* All diagnostic output is directed to `stderr` to avoid interfering with Zabbix's internal parsing.

## Prerequisites

* **Python 3** installed on your Zabbix Server.
* **`curl`** command-line tool available on your Zabbix Server.
* **GLPI Instance** with REST API enabled.
* **GLPI App Token** and a **GLPI User Token** with sufficient permissions to create tickets. The GLPI user associated with the User Token must have "Create" permission for "Tickets" in their profile.

## Setup

### 1. Script Placement

Place the `curl_zabbix_glpi_ticket.py` script in your Zabbix alert scripts directory.
Typically: `/usr/lib/zabbix/alertscripts/`

```bash
sudo cp curl_zabbix_glpi_ticket.py /usr/lib/zabbix/alertscripts/
sudo chmod +x /usr/lib/zabbix/alertscripts/curl_zabbix_glpi_ticket.py  
