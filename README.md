# Dvg-Sprint-4 – Rechnungsverarbeitung mit Camunda 8

**Hochschule Karlsruhe** | Modul: Digitalisierung von Geschäftsprozessen | Gruppe G11

---

## Was ist das hier?

Sprint 4 baut auf dem Sprint-2-Backend auf und verbindet es mit einem echten BPMN-Prozess in Camunda 8 SaaS. Rechnungen laufen jetzt durch einen modellierten Workflow — mit automatischen Prüfungen, manuellen Aufgaben und Fehlerbehandlung wenn ein Dienst nicht erreichbar ist.

---

## Projektstruktur

```
Dvg-sprint-4/
├── src/
│   ├── workers/
│   │   ├── auto_workers.py        # Automatische Camunda Job Worker
│   │   ├── grpc_worker.py         # Worker für Metadaten per gRPC
│   │   └── payment_worker.py      # Worker für Zahlung per RabbitMQ
│   ├── invoice_metadata/
│   │   ├── server.py              # gRPC Server (aus Sprint 2)
│   │   ├── invoice.proto          # Protobuf Definition
│   │   ├── invoice_pb2.py
│   │   └── invoice_pb2_grpc.py
│   ├── payment_system/
│   │   └── payment.py             # RabbitMQ Consumer (aus Sprint 2)
│   └── camunda/
│       └── compliance_check.dmn   # DMN Entscheidungstabelle
├── tests/
│   └── test_workers.py
├── extras/
│   └── compose/
│       ├── RabbitMQ/docker-compose.yml
│       └── postgres/docker-compose.yml
├── docs/
│   └── documentation.md
├── start_process.py
├── send_correction.py
├── .env
├── requirements.txt
└── README.md
```

---

## Voraussetzungen

- Python 3.10+
- Docker
- Camunda 8 SaaS Account

```bash
pip install -r requirements.txt
```

---

## Einrichtung

### 1. Umgebungsvariablen

`.env` Datei im Projektroot anlegen:

```
CAMUNDA_CLIENT_ID=...
CAMUNDA_CLIENT_SECRET=...
CAMUNDA_CLUSTER_ID=...
CAMUNDA_REGION=bru-2

GRPC_HOST=localhost
GRPC_PORT=50051

RABBITMQ_HOST=localhost
RABBITMQ_USER=user
RABBITMQ_PASSWORD=password

DB_HOST=localhost
DB_NAME=invoice_db
DB_USER=admin
DB_PASSWORD=...
```

### 2. Docker starten

```bash
cd extras/compose/postgres && docker-compose up -d
cd extras/compose/RabbitMQ && docker-compose up -d
```

---

## Starten

**Terminal 1** – gRPC Server:
```bash
python -m src.invoice_metadata.server
```

**Terminal 2** – Auto Workers:
```bash
python src/workers/auto_workers.py
```

**Terminal 3** – gRPC Worker:
```bash
python src/workers/grpc_worker.py
```

**Terminal 4** – Payment Worker:
```bash
python src/workers/payment_worker.py
```

**Prozess starten:**
```bash
python start_process.py
```

---

## Tests

```bash
$env:PYTHONPATH = "."; pytest tests/test_workers.py -v
```

---

## Prozessablauf

Der Prozess heißt **Workflow-Sprint-4** in Camunda 8 SaaS.

**Normalfall (Email):**
Rechnung eingang → Metadaten manuell extrahieren → Rechnung validieren → Compliance Check → Rechnung freigeben → gRPC speichern → ERP eingeben → RabbitMQ Zahlung → Archivieren

**Fehlerfall gRPC:**
gRPC Server nicht erreichbar → Boundary Error → Metadaten manuell speichern

**Fehlerfall RabbitMQ:**
RabbitMQ nicht erreichbar → Boundary Error → Zahlung manuell erfassen

**Compliance-Verstoß:**
Betrag über Schwellenwert → Compliance manuell prüfen → Freigeben oder Zurückweisen

---

## Compliance-Schwellenwerte

| Währung | Schwellenwert |
|---------|--------------|
| EUR     | > 10.000     |
| USD     | > 11.000     |
| CHF     | > 10.800     |
| GBP     | > 8.700      |

---

## Korrektur senden

Wenn ein Prozess auf fehlende Informationen wartet:

```bash
python send_correction.py R-001
```
