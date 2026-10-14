import torch
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32
model = SentenceTransformer("google/embeddinggemma-2", model_kwargs={"torch_dtype": dtype}, device=device)

query = "What causes the northern lights?"
related = "The northern lights are caused by charged particles from the sun."
unrelated = "A recipe for potato salad with spring onions."

q = model.encode(query, prompt_name="SearchQuery")
print("related text  :", round(float(model.similarity(q, model.encode(related, prompt_name="Document"))), 2))
print("unrelated text:", round(float(model.similarity(q, model.encode(unrelated, prompt_name="Document"))), 2))
