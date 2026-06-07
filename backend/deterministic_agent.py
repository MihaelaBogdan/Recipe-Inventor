"""
deterministic_agent.py
----------------------
A rule-based pseudo-agent that simulates Iterative RAG (Agentic Retrieval) 
without an LLM. It analyzes RAG scores and rewrites queries if needed.
"""

from typing import List, Dict, Any

class DeterministicAgent:
    def __init__(self, rag_engine):
        self.rag_engine = rag_engine
        self.MIN_SCORE_THRESHOLD = 0.55
        self.MAX_ITERATIONS = 3
        
    def run_agentic_retrieval(
        self, 
        original_ingredients: List[str], 
        filters: Dict[str, Any],
        method: str = "hybrid",
        alpha: float = 0.7,
        threshold: float = 0.55,
        use_mmr: bool = False,
        mmr_lambda: float = 0.5
    ) -> Dict[str, Any]:
        """
        Runs the iterative retrieval loop using customizable RAG configurations.
        """
        logs = []
        current_ingredients = list(original_ingredients)
        
        logs.append(
            f"Agent started. Strategy: {method.upper()} | "
            f"Alpha: {alpha:.2f} | Threshold: {threshold:.2f} | "
            f"MMR: {use_mmr} (λ={mmr_lambda:.2f})"
        )
        logs.append(f"Initial ingredients: {', '.join(current_ingredients)}")
        
        top_recipes = []
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            logs.append(f"[Iteration {iteration}] Formulating query and searching local DB...")
            
            # Formulate query
            query = " ".join(current_ingredients)
            
            # Execute customized RAG retrieval (use threshold=0.0 inside engine so the agent can check the raw score and decide whether to rewrite/fallback)
            res = self.rag_engine.retrieve_custom(
                query=query,
                method=method,
                alpha=alpha,
                threshold=0.0,
                use_mmr=use_mmr,
                mmr_lambda=mmr_lambda,
                filters=filters,
                top_k=5
            )
            
            top_recipes = res["recipes"]
            
            if not top_recipes:
                logs.append("️ No recipes found for this query in the database.")
                if len(current_ingredients) > 1:
                    dropped = current_ingredients.pop()
                    logs.append(f"Action: Dropping '{dropped}' from query to expand search space.")
                    continue
                else:
                    logs.append("Action: Cannot drop more ingredients. Aborting.")
                    break
                
            best_recipe = top_recipes[0]
            best_score = best_recipe.get("retrieval_score", 0.0)
            
            logs.append(f"Top result: '{best_recipe.get('title')}' with Confidence Score: {best_score:.3f}")
            
            if best_score >= threshold:
                logs.append(f" Score {best_score:.3f} is above threshold ({threshold:.2f}). Retrieval successful!")
                return {"recipes": top_recipes, "logs": logs}
            else:
                logs.append(f"️ Score {best_score:.3f} is below target threshold ({threshold:.2f}).")
                logs.append("Self-critique: The query ingredients might be too restrictive.")
                if len(current_ingredients) > 1:
                    dropped = current_ingredients.pop()
                    logs.append(f"Action: Dropping '{dropped}' from query to broaden search.")
                else:
                    logs.append("Action: Reached single ingredient limit. Cannot drop further.")
                    break
                    
        logs.append("Max iterations reached or query minimized. Returning best effort results.")
        return {"recipes": top_recipes, "logs": logs}
