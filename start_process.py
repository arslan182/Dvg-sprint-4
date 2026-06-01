import os
import asyncio
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
from dotenv import load_dotenv

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

PROZESS_ID = "Process_workflow_sprint4"

VARIABLEN = {
    "eingangskanal": "email",
    "rechnungs_nummer": "R-001",
    "lieferant": "Mustermann GmbH",
    "betrag": 5000,
    "waehrung": "EUR",
    "datum": "2026-06-01",
    "rechnung_genehmigt": True,
    "informationen_erhalten": True,
}


async def main():
    print("\n" + "=" * 55)
    print("  Dvg Sprint 4 – Prozess starten")
    print("=" * 55)
    print(f"\n  Starte Prozess mit folgenden Variablen:")
    for k, v in VARIABLEN.items():
        print(f"    {k}: {v}")
    print()

    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )

    client = ZeebeClient(channel)
    instance = await client.run_process(
        bpmn_process_id=PROZESS_ID,
        variables=VARIABLEN,
    )

    print(f"Prozess gestartet!")
    print(f"Process Instance Key: {instance.process_instance_key}")
    print(f"Operate: https://operate.camunda.io/{CAMUNDA_CLUSTER_ID}/processes/{instance.process_instance_key}")

    await channel.close()


if __name__ == "__main__":
    asyncio.run(main())
