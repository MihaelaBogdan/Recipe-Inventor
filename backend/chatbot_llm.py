class RecipeChatbotLLM:
    def __init__(self, rag_engine, agent, llm):
        self.rag = rag_engine
        self.agent = agent
        self.llm = llm

    def build_context(self, recipes):
        if not recipes:
            return "Nu am găsit rețete relevante."

        context = []
        for r in recipes[:5]:
            context.append(
                f"""
Title: {r.get('title')}
Cuisine: {r.get('cuisine')}
Difficulty: {r.get('difficulty')}
Ingredients: {', '.join(r.get('ingredients', []))}
Time: {r.get('time', 'unknown')}
"""
            )
        return "\n".join(context)

    def respond(self, message: str):
        # 1. retrieval (simplu sau agentic)
        result = self.agent.run_agentic_retrieval(
            original_ingredients=[message],
            filters={"cuisine": "Any", "difficulty": "Any", "max_time": None},
            method="hybrid",
        )

        recipes = result["recipes"]

        # 2. context
        context = self.build_context(recipes)

        # 3. prompt pentru LLM
        prompt = f"""
You are a cooking assistant.

Use the recipes below as context:

{context}

User question:
{message}

Rules:
- Answer ONLY using the context if possible
- If not enough info, say so
- Be concise and helpful
"""

        # 4. generate
        return self.llm.generate(prompt)