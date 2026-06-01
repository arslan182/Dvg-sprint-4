import os
import grpc
from concurrent import futures
import psycopg2
from dotenv import load_dotenv
from . import invoice_pb2
from . import invoice_pb2_grpc

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "invoice_db")
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secretpassword")


class RechnungService(invoice_pb2_grpc.RechnungServiceServicer):
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self._create_table()

    def _create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    rechnungs_nummer VARCHAR(50) PRIMARY KEY,
                    lieferant VARCHAR(100),
                    betrag DOUBLE PRECISION,
                    waehrung VARCHAR(10),
                    datum DATE,
                    status VARCHAR(20)
                );
            """)
            self.conn.commit()

    def SpeichereMetadaten(self, request, context):
        status_name = invoice_pb2.RechnungsStatus.Name(request.status)

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO invoices (rechnungs_nummer, lieferant, betrag, waehrung, datum, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rechnungs_nummer) DO UPDATE
                    SET status = EXCLUDED.status;
                """, (
                    request.rechnungs_nummer,
                    request.lieferant,
                    request.betrag,
                    request.waehrung,
                    request.datum,
                    status_name
                ))
                self.conn.commit()

            print(f"[DB] Rechnung {request.rechnungs_nummer} gespeichert.")
            return invoice_pb2.RechnungResponse(erfolg=True, nachricht="In DB gespeichert")

        except Exception as e:
            print(f"[DB] Fehler: {e}")
            return invoice_pb2.RechnungResponse(erfolg=False, nachricht=str(e))


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    invoice_pb2_grpc.add_RechnungServiceServicer_to_server(RechnungService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("[gRPC Server] Läuft auf Port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
