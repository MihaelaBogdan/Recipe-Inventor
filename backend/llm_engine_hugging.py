from transformers import AutoTokenizer, AutoModelForCausalLM
import torch



class LLMEngineHugging:

    def __init__(self):

        model_name = "Qwen/Qwen2.5-3B-Instruct"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def generate(self, prompt, max_new_tokens=300):

        messages = [
            {"role": "system", "content": "You are a helpful cooking assistant."},
            {"role": "user", "content": prompt}
        ]
    
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
    
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
    
        # 🔥 IMPORTANT FIX: decode ONLY NEW TOKENS
        input_len = inputs["input_ids"].shape[1]
    
        generated_tokens = outputs[0][input_len:]
    
        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )
    
        return response.strip()