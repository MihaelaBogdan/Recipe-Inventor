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
        #print("RECIPES FROM CHROMA:")
        #for r in recipes:
            #print(r)

        # 2. context
        #context = self.build_context(recipes) # simple context builder, just concatenating recipe info
        context_parts = []

        for r in recipes:
            context_parts.append(f"""
        Recipe: {r['title']}

        Cuisine: {r.get('cuisine')}
        Difficulty: {r.get('difficulty')}
        Time: {r.get('time_minutes')} minutes

        Ingredients:
        - """ + "\n- ".join(r.get('ingredients', [])) + """

        Steps:
        - """ + "\n- ".join(r.get('steps', [])) + """

        Tags: {r.get('tags')}
        ---
        """)

        context = "\n".join(context_parts)

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
- You can combine different recipes from context,think of alternative ingredients, suggest modifications, but only based on the context provided. Do not hallucinate any information that is not present in the context.
- Do not make up recipes or details that are not in the context
- Provide answers in the language which you are asked in (English or Romanian)
- If the context is empty, say you couldn't find relevant recipes
- Speak very detailed about recipes and steps, as if you are an expert chef, but only based on the context provided. Do not hallucinate any information that is not present in the context.
- Take the freedom to suggest recipe recommendations, replacing, ingredient replacing.You can base yourself out of context if the context is not sufficient, but you should always try to use the context as much as possible. You can also suggest general cooking tips and tricks, but again only if the context is not sufficient to answer the question. Always try to use the context as much as possible.
- Always go out of context if there is not enough information, but specify when doing so.
"""

        # 4. generate
        return self.llm.generate(prompt)