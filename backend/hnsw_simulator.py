"""
HNSW Simulator - Visual Graph Traversal for Recipe Search
Simulates the Hierarchical Navigable Small World algorithm
"""
import numpy as np
from typing import List, Dict, Tuple, Set
import random

class HNSWSimulator:
    """Simulates HNSW graph traversal for visualizing recipe search"""

    def __init__(self, recipes: List[Dict], embeddings_map: Dict[str, np.ndarray], encoder):
        self.recipes = recipes
        self.embeddings_map = embeddings_map  # recipe_id -> embedding vector
        self.encoder = encoder
        self.M = 16  # Max connections per node
        self.ef_construction = 200
        self.ef_search = 30  # Increased for better exploration
        self.ml = 1.0 / np.log(2.0)

        # Build HNSW graph structure
        self.graph = self._build_graph()
        self.layers = self._assign_layers()
        self.max_layer = max(self.layers.values()) if self.layers else 0

    def _build_graph(self) -> Dict:
        """Build adjacency list for HNSW graph"""
        graph = {}
        recipe_ids = [str(r["id"]) for r in self.recipes]

        for rid in recipe_ids:
            graph[rid] = {"neighbors": []}

        # Connect recipes based on embedding similarity
        embeddings = np.array([self.embeddings_map.get(rid, np.zeros(384)) for rid in recipe_ids])

        for i, rid1 in enumerate(recipe_ids):
            emb1 = embeddings[i]
            if np.sum(emb1) == 0:
                continue

            # Find M nearest neighbors
            distances = []
            for j, rid2 in enumerate(recipe_ids):
                if i != j:
                    emb2 = embeddings[j]
                    if np.sum(emb2) > 0:
                        try:
                            sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8)
                            dist = 1 - max(0, sim)  # Convert similarity to distance
                            distances.append((dist, rid2))
                        except:
                            pass

            # Sort by distance and keep M nearest
            distances.sort()
            neighbors = [rid for _, rid in distances[:self.M * 2]]  # Keep more neighbors
            graph[rid1]["neighbors"] = neighbors

        return graph

    def _assign_layers(self) -> Dict[str, int]:
        """Assign layers to nodes using exponential distribution"""
        layers = {}
        recipe_ids = [str(r["id"]) for r in self.recipes]

        # Layer 0: All recipes (100%)
        for rid in recipe_ids:
            layers[rid] = 0

        # Layer 1: ~40% of recipes
        layer1_count = max(2, int(len(recipe_ids) * 0.40))
        layer1_recipes = random.sample(recipe_ids, layer1_count)
        for rid in layer1_recipes:
            layers[rid] = 1

        # Layer 2: ~15% of recipes
        layer2_count = max(1, int(len(recipe_ids) * 0.15))
        layer2_recipes = random.sample(layer1_recipes, min(layer2_count, len(layer1_recipes)))
        for rid in layer2_recipes:
            layers[rid] = 2

        # Layer 3: ~5% of recipes
        layer3_count = max(1, int(len(recipe_ids) * 0.05))
        layer3_recipes = random.sample(layer2_recipes, min(layer3_count, len(layer2_recipes)))
        for rid in layer3_recipes:
            layers[rid] = 3

        # Layer 4: ~2% of recipes (entry points)
        layer4_count = max(1, int(len(recipe_ids) * 0.02))
        layer4_recipes = random.sample(layer3_recipes, min(layer4_count, len(layer3_recipes)))
        for rid in layer4_recipes:
            layers[rid] = 4

        return layers

    def simulate_search(self, query: str, target_recipe_id: str = None) -> Dict:
        """
        Simulate HNSW search for a query
        Returns: path taken, nodes visited, similarity scores at each step
        """
        # Encode query
        query_embedding = self.encoder.encode(query)

        # Select entry point (from layer 2)
        layer2_recipes = [rid for rid, layer in self.layers.items() if layer == 2]
        if not layer2_recipes:
            layer2_recipes = [str(r["id"]) for r in self.recipes[:1]]

        entry_point = random.choice(layer2_recipes)
        entry_recipe = next((r for r in self.recipes if str(r["id"]) == entry_point), None)

        if not entry_recipe:
            return {"error": "No recipes available"}

        path = []
        visited = set()
        layer_transitions = []

        # Start from entry point
        current_node = entry_point
        current_layer = self.layers.get(current_node, 0)
        visited.add(current_node)

        current_recipe = entry_recipe
        current_embedding = self.embeddings_map.get(current_node, np.zeros(384))
        current_similarity = self._calculate_similarity(query_embedding, current_embedding)

        path.append({
            "node": current_node,
            "recipe_title": current_recipe.get("title", "Unknown"),
            "layer": current_layer,
            "similarity": float(current_similarity),
            "is_entry": True,
            "is_target": current_node == str(target_recipe_id) if target_recipe_id else False
        })

        layer_transitions.append({
            "from_layer": current_layer,
            "to_layer": current_layer,
            "step": 0
        })

        # Traverse layers top-down with more thorough exploration
        current_candidates: List[Tuple[float, str]] = [(current_similarity, current_node)]

        for target_layer in range(current_layer - 1, -1, -1):
            new_candidates: List[Tuple[float, str]] = []

            # Explore ef_search candidates at each layer
            for _, candidate in current_candidates[:self.ef_search]:
                if candidate not in self.graph:
                    continue

                neighbors = self.graph[candidate].get("neighbors", [])

                for neighbor in neighbors:
                    if neighbor in visited:
                        continue

                    neighbor_recipe = next((r for r in self.recipes if str(r["id"]) == neighbor), None)
                    if not neighbor_recipe:
                        continue

                    neighbor_layer = self.layers.get(neighbor, 0)

                    # Only consider neighbors at or below target layer
                    if neighbor_layer < target_layer:
                        continue

                    neighbor_embedding = self.embeddings_map.get(neighbor, np.zeros(384))
                    neighbor_similarity = self._calculate_similarity(query_embedding, neighbor_embedding)

                    # Add to path if new
                    if neighbor not in visited:
                        visited.add(neighbor)
                        path.append({
                            "node": neighbor,
                            "recipe_title": neighbor_recipe.get("title", "Unknown"),
                            "layer": neighbor_layer,
                            "similarity": float(neighbor_similarity),
                            "is_entry": False,
                            "is_target": neighbor == str(target_recipe_id) if target_recipe_id else False
                        })

                        new_candidates.append((neighbor_similarity, neighbor))

                        if len(path) > 1 and neighbor_layer != path[-2].get("layer", 0):
                            layer_transitions.append({
                                "from_layer": path[-2].get("layer", 0),
                                "to_layer": neighbor_layer,
                                "step": len(path) - 1
                            })

            # Keep best candidates for next layer
            new_candidates.sort(reverse=True)
            current_candidates = new_candidates[:self.ef_search]

            # If no more candidates, break
            if not current_candidates:
                break

            current_node = current_candidates[0][1]

        # Collect candidates at layer 0 (final neighbors)
        final_candidates = []
        if current_node in self.graph:
            for neighbor in self.graph[current_node]["neighbors"][:self.ef_search]:
                neighbor_recipe = next((r for r in self.recipes if str(r["id"]) == neighbor), None)
                if neighbor_recipe:
                    neighbor_embedding = self.embeddings_map.get(neighbor, np.zeros(384))
                    neighbor_similarity = self._calculate_similarity(query_embedding, neighbor_embedding)

                    final_candidates.append({
                        "node": neighbor,
                        "recipe_title": neighbor_recipe.get("title", "Unknown"),
                        "ingredients": neighbor_recipe.get("ingredients", [])[:6],  # First 6 ingredients
                        "cuisine": neighbor_recipe.get("cuisine", ""),
                        "layer": 0,
                        "similarity": float(neighbor_similarity),
                        "is_target": neighbor == str(target_recipe_id) if target_recipe_id else False
                    })

        final_candidates.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "query": query,
            "entry_point": entry_point,
            "entry_recipe": entry_recipe.get("title", "Unknown") if entry_recipe else "Unknown",
            "path": path,
            "visited_nodes": list(visited),
            "layer_transitions": layer_transitions,
            "final_candidates": final_candidates[:self.ef_search],
            "total_steps": len(path),
            "parameters": {
                "M": self.M,
                "efSearch": self.ef_search,
                "efConstruction": self.ef_construction
            }
        }

    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get_layer_nodes(self, layer: int) -> List[Dict]:
        """Get all nodes at a specific layer"""
        nodes = []
        for rid in self.layers:
            if self.layers[rid] == layer:
                recipe = next((r for r in self.recipes if str(r["id"]) == rid), None)
                if recipe:
                    embedding = self.embeddings_map.get(rid, np.zeros(384))
                    nodes.append({
                        "id": rid,
                        "title": recipe.get("title", "Unknown"),
                        "layer": layer,
                        "embedding": embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                    })
        return nodes

    def get_graph_stats(self) -> Dict:
        """Get statistics about the HNSW graph"""
        layer_counts = {}
        for layer in self.layers.values():
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

        return {
            "total_nodes": len(self.recipes),
            "layer_distribution": layer_counts,
            "parameters": {
                "M": self.M,
                "efSearch": self.ef_search,
                "efConstruction": self.ef_construction,
                "ml": float(self.ml)
            }
        }
