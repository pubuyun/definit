from parser.models.question import Question, SubQuestion, SubSubQuestion
from parser.models.answer import MarkScheme
from typing import Any, Dict, List, Optional
from transformers import AutoTokenizer, AutoModel
import torch
from torch.nn.functional import cosine_similarity

# 加载 SciBERT 模型
tokenizer = AutoTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = AutoModel.from_pretrained("allenai/scibert_scivocab_uncased")




class Classifier:
    def __init__(self, syllabus):
        
    
    @staticmethod
    def get_sentence_embedding(sentence):
        inputs = tokenizer(sentence, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # shape: (1, hidden_size)
        return cls_embedding.squeeze()