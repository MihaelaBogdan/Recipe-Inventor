import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Încarcă modelul de embeddings local (on-premise)
print("🔌 Se încarcă modelul local 'all-MiniLM-L6-v2'...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model încărcat cu succes!")

# 2. Transformă un text într-un vector (Embedding)
text = "paste cu sos de rosii"
print(f"\n📝 Convertim textul: '{text}' în vector...")
vector = model.encode([text])[0]

# Inspectăm structura vectorului obținut
print("-" * 50)
print(f"📐 Dimensiunea vectorului (Shape): {vector.shape} de elemente (dimensiuni)")
print(f"🔢 Primele 10 numere (dimensiuni) din vector:\n{vector[:10]}")
print(f"ℹ️ Acest vector reprezintă amprenta semantică a textului pe plan local.")
print("-" * 50)

# 3. Calculăm similaritatea semantică între propoziții
text_a = "Spaghete cu sos tomat si busuioc"
text_b = "Paste fainoase cu sos din tomate proaspete"
text_c = "Cum repar motorul mașinii în garaj"

print("\n🔬 Testăm similaritatea semantică:")
print(f"   A: '{text_a}'")
print(f"   B: '{text_b}' (înțeles similar)")
print(f"   C: '{text_c}' (înțeles complet diferit)")

# Generăm vectorii
emb_a = model.encode([text_a])[0]
emb_b = model.encode([text_b])[0]
emb_c = model.encode([text_c])[0]

# Funcție pentru distanța Cosinus
def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

# Calculăm scorurile
sim_ab = cosine_similarity(emb_a, emb_b)
sim_ac = cosine_similarity(emb_a, emb_c)

print("-" * 50)
print(f"📈 Similaritate A cu B (semantice apropiate): {sim_ab:.4f} (~ 70% - 90%)")
print(f"📉 Similaritate A cu C (complet diferite):    {sim_ac:.4f} (~ 0% - 15%)")
print("-" * 50)
