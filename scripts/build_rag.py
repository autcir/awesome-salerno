#!/usr/bin/env python3
"""Build a RAG-ready dataset from the POI data.

One POI = one chunk. POI records are already short and self-contained, so
splitting them would only break the text away from its coordinates.

    python3 scripts/build_rag.py              # write data/rag/chunks.jsonl
    python3 scripts/build_rag.py --qdrant     # also upsert into Qdrant

Qdrant upload needs `pip install "qdrant-client[fastembed]"` and honours
QDRANT_URL (default http://localhost:6333), QDRANT_API_KEY,
QDRANT_COLLECTION (default awesome-salerno) and QDRANT_MODEL.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "rag" / "chunks.jsonl"
# multilingual: the POI text is Italian
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CATEGORIES = ["sentieri", "monumenti", "spiagge", "eventi", "panorami", "parchi"]

# singular label used in the chunk text, so the embedding carries the category
LABEL = {"sentieri": "Sentiero", "monumenti": "Monumento", "spiagge": "Spiaggia",
         "eventi": "Evento", "panorami": "Panorama", "parchi": "Parco"}


def to_text(cat, it):
    parts = [f"{LABEL[cat]}: {it.get('nome', '')}"]
    where = ", ".join(x for x in (it.get("quartiere"), it.get("citta"), it.get("zona")) if x)
    if where:
        parts.append(f"Dove: {where}")
    if it.get("tipo") and it["tipo"] != "altro":
        parts.append(f"Tipo: {it['tipo']}")
    if it.get("data_inizio"):
        d = it["data_inizio"]
        if it.get("data_fine") and it["data_fine"] != d:
            d += f" - {it['data_fine']}"
        parts.append(f"Date: {d}")
    if it.get("ricorrenza"):
        parts.append(f"Ricorrenza: {it['ricorrenza']}")
    if it.get("descrizione"):
        parts.append(it["descrizione"])
    if it.get("luoghi"):
        parts.append("Luoghi: " + ", ".join(it["luoghi"]))
    return ". ".join(parts)


def build():
    chunks = []
    for cat in CATEGORIES:
        for it in json.loads((DATA / f"{cat}.json").read_text()):
            chunks.append({
                "id": it["id"],
                "text": to_text(cat, it),
                "categoria": cat,
                "nome": it.get("nome"),
                "tipo": it.get("tipo"),
                "zona": it.get("zona"),
                "citta": it.get("citta"),
                "quartiere": it.get("quartiere"),
                "lat": it.get("lat"),
                "lng": it.get("lng"),
                "link": it.get("link"),
                "last_verified": it.get("last_verified"),
            })
    return chunks


def point_id(poi_id):
    """Stable numeric id: Python's hash() is salted per process, re-running
    it would upsert duplicates instead of overwriting."""
    return int.from_bytes(hashlib.blake2b(poi_id.encode(), digest_size=8).digest()) >> 1


def to_qdrant(chunks):
    from fastembed import TextEmbedding
    from qdrant_client import QdrantClient, models

    name = os.getenv("QDRANT_COLLECTION", "awesome-salerno")
    model_name = os.getenv("QDRANT_MODEL", MODEL)
    embedder = TextEmbedding(model_name)
    dim = TextEmbedding._get_model_description(model_name).dim

    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                          api_key=os.getenv("QDRANT_API_KEY"), timeout=120)
    if not client.collection_exists(name):
        client.create_collection(name, vectors_config=models.VectorParams(
            size=dim, distance=models.Distance.COSINE))
        # payload indexes: a retriever filters by these before it ranks
        for field in ("categoria", "tipo", "zona", "citta", "quartiere"):
            client.create_payload_index(name, field, models.PayloadSchemaType.KEYWORD)

    vectors = embedder.embed([c["text"] for c in chunks], batch_size=64)
    batch = []
    done = 0
    for chunk, vec in zip(chunks, vectors):
        batch.append(models.PointStruct(id=point_id(chunk["id"]),
                                        vector=vec.tolist(), payload=chunk))
        if len(batch) == 256:
            client.upsert(name, batch, wait=False)
            done += len(batch)
            batch = []
            print(f"  {done}/{len(chunks)}", end="\r", flush=True)
    if batch:
        client.upsert(name, batch, wait=True)
        done += len(batch)
    print(f"upserted {done} points into '{name}' ({model_name}, dim {dim})")


def main():
    chunks = build()
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"{len(chunks)} chunks -> {OUT.relative_to(ROOT)} "
          f"({OUT.stat().st_size // 1024} KB)")
    if "--qdrant" in sys.argv:
        to_qdrant(chunks)


def demo():
    ev = {"nome": "Luci d'Artista", "citta": "Salerno", "zona": "salerno",
          "quartiere": "Centro Storico", "tipo": "luci-artista",
          "data_inizio": "2025-11-14", "data_fine": "2026-02-01",
          "ricorrenza": "annuale", "descrizione": "Installazioni luminose.",
          "luoghi": ["Lungomare"]}
    t = to_text("eventi", ev)
    assert t.startswith("Evento: Luci d'Artista")
    assert "Centro Storico, Salerno, salerno" in t
    assert "2025-11-14 - 2026-02-01" in t
    assert "Luoghi: Lungomare" in t
    assert to_text("parchi", {"nome": "X", "tipo": "altro"}) == "Parco: X"
    assert point_id("luci-dartista-2025") == point_id("luci-dartista-2025")
    assert point_id("a") != point_id("b")
    print("ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
