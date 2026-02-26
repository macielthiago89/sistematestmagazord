import csv
import random
from pathlib import Path

def generate(path: str, rows: int = 10):
    # Robot pode passar rows como string, então força int aqui:
    rows_i = int(rows)

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # DEBUG: grava também um arquivo .meta para provar quantas linhas foram solicitadas
    meta = p.with_suffix(".meta.txt")
    meta.write_text(f"requested_rows={rows_i}\n", encoding="utf-8")

    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")  # ; ajuda no Excel PT-BR
        w.writerow(["nome", "email", "idade", "cidade"])
        for i in range(rows_i):
            w.writerow([
                f"User {i}",
                f"user{i}@email.com",
                random.randint(18, 70),
                random.choice(["São Paulo", "Rio de Janeiro", "Fortaleza"])
            ])

    return str(p.resolve())