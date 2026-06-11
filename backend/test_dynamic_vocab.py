import sys
import os
sys.path.append(os.path.dirname(__file__))

import numpy as np
from sentence_transformers import SentenceTransformer
from recipes_data import BASE_RECIPES
import string

print("Loading model...")
encoder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# Build vocab
stop_words = {"with", "and", "the", "for", "in", "of", "a", "an", "to", "or", "at", "by", "from", "on", "fresh", "ground", "chopped", "sliced", "diced", "powder", "taste", "salt", "pepper"}
vocab = set()
for r in BASE_RECIPES:
    text = (r.get("title", "") + " " + " ".join(r.get("ingredients", []))).lower()
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
    for word in text.split():
        if len(word) > 2 and word.isalpha() and word not in stop_words:
            vocab.add(word)
            
english_vocab = sorted(list(vocab))
print(f"Vocab size: {len(english_vocab)}")

# Embed vocab
vocab_embeddings = encoder.encode(english_vocab)

# Test query words
for w in ["pui", "usturoi"]:
    w_emb = encoder.encode([w])
    dots = np.dot(vocab_embeddings, w_emb[0])
    norms_vocab = np.linalg.norm(vocab_embeddings, axis=1)
    norm_w = np.linalg.norm(w_emb[0])
    
    similarities = dots / (norms_vocab * norm_w)
    
    # Check if 'chicken' is in vocab and print its score
    if "chicken" in english_vocab:
        c_idx = english_vocab.index("chicken")
        print(f"  -> 'chicken' is in vocab at index {c_idx}, similarity: {similarities[c_idx]:.4f}")
    else:
        print("  -> 'chicken' is NOT in vocab!")
        
    # Sort similarities
    top_indices = np.argsort(similarities)[::-1][:10]
    print(f"\nTop 10 matches for '{w}':")
    for idx in top_indices:
        print(f"  {english_vocab[idx]}: {similarities[idx]:.4f}")
