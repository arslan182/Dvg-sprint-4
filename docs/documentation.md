# Dokumentation – Sprint 4

**Modul:** Digitalisierung von Geschäftsprozessen  
**Hochschule:** Hochschule Karlsruhe  
**Gruppe:** G11

---

## Ziel von Sprint 4

In Sprint 4 haben wir den Rechnungsverarbeitungsprozess als ausführbaren BPMN-Workflow in Camunda 8 SaaS modelliert und mit den Diensten aus Sprint 2 verbunden. Damit läuft der gesamte Prozess — von der Rechnungserfassung bis zur Archivierung — orchestriert durch Camunda.

---

## Architektur

```
Camunda 8 SaaS (BPMN-Prozess)
        │
        │  Zeebe Jobs
        ▼
  Python Worker (pyzeebe)
   ├── auto_workers.py   → automatische Service Tasks
   ├── grpc_worker.py    → Metadaten per gRPC speichern
   └── payment_worker.py → Zahlung per RabbitMQ senden
        │
        ├──▶ gRPC Server → PostgreSQL Datenbank
        └──▶ RabbitMQ Queue → Payment Consumer
```

---

## BPMN-Prozess

Der Prozess **Workflow-Sprint-4** bildet den kompletten Purchase-to-Pay Ablauf ab.

### Eingangskanäle

Rechnungen können auf zwei Wegen eingehen:

- **EDI** – vollautomatisch, direkt zur Validierung
- **Email / Portal** – manuell, Sachbearbeiter extrahiert die Daten

### Automatische Tasks

Diese Tasks werden von den Python-Workern verarbeitet, ohne dass ein Mensch eingreifen muss:

| Task | Worker | Beschreibung |
|------|--------|--------------|
| rechnung-erfassen | auto_workers.py | Zeitstempel und Status setzen |
| automatische-validierung | auto_workers.py | Pflichtfelder prüfen |
| compliance-check | auto_workers.py | Schwellenwert prüfen |
| save-invoice-metadata | grpc_worker.py | Metadaten per gRPC speichern |
| initiate-payment | payment_worker.py | Zahlungsauftrag per RabbitMQ |
| rechnung-archivieren | auto_workers.py | Archivieren |

### Manuelle Tasks (User Tasks)

Diese Tasks erscheinen in der Camunda Tasklist und müssen von einem Sachbearbeiter bearbeitet werden:

- Metadaten aus Rechnung manuell extrahieren
- Rechnung Validieren
- Compliance-Fall manuell prüfen
- Rechnung freigeben
- Rechnungsdaten im ERP-System eingeben

### Fehlerbehandlung (Boundary Error Events)

Wenn ein automatischer Dienst nicht erreichbar ist, fängt ein Boundary Error Event den Fehler ab und leitet den Prozess in einen manuellen Fallback:

- **gRPC nicht erreichbar** → „Metadaten manuell speichern"
- **RabbitMQ nicht erreichbar** → „Zahlung manuell erfassen"

Das funktioniert über `BusinessError` aus der pyzeebe-Bibliothek. Normale Python-Exceptions reichen dafür nicht — Camunda braucht explizit einen BPMN-Fehler.

---

## Compliance-Prüfung

Der Compliance-Check läuft automatisch und vergleicht den Rechnungsbetrag mit währungsspezifischen Schwellenwerten:

| Währung | Schwellenwert |
|---------|--------------|
| EUR     | 10.000       |
| USD     | 11.000       |
| CHF     | 10.800       |
| GBP     | 8.700        |

Liegt der Betrag darüber, wird `compliance_notwendig = true` gesetzt und der Prozess geht zum manuellen User Task „Compliance-Fall manuell prüfen".

---

## Verbindung zu Sprint 2

| Sprint 2 Dienst | Verwendet von |
|-----------------|---------------|
| gRPC Server (Port 50051) | grpc_worker.py |
| PostgreSQL Datenbank | gRPC Server, Payment Consumer |
| RabbitMQ Queue `zahlungs_auftraege` | payment_worker.py |
| Payment Consumer | Liest aus RabbitMQ, setzt Status in DB |

---

## Bekannte Einschränkungen

- Der Camunda Trial Cluster pausiert automatisch nach längerer Inaktivität. Vor dem Testen prüfen ob der Cluster läuft.
- Prozessvariablen die vom Worker gesetzt werden (z.B. `validierung_erfolgreich`, `compliance_notwendig`) sollten beim Start nicht manuell mitgegeben werden — der Worker überschreibt sie sowieso.
- Das Formular-Dropdown in Camunda speichert Werte als String. Deswegen haben wir für `rechnung_freigegeben` auf eine Checkbox umgestellt, die echte Boolean-Werte liefert.

---

## Unit Tests

Die Tests prüfen die Worker-Logik ohne Camunda-Verbindung:

```bash
$env:PYTHONPATH = "."; pytest tests/test_workers.py -v
```

Getestet wird: Validierung (gültige und ungültige Eingaben), Compliance-Schwellenwerte für alle vier Währungen, Grundfunktion der Erfassung.
