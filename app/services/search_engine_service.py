import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import torch
from langdetect import detect

class SearchService:
    def __init__(self):
        self.model_loaded = False  # Flag to check if models are loaded

    def load_models(self):
        # Load models for English and French
        self.english_model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')
        self.french_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Load and process all PDFs from the 'data' folder
        folder_path = os.path.join(os.path.dirname(__file__), '../data_search')
        self.documents = self.extract_text_from_pdfs(folder_path)

        # Precompute document embeddings for English and French
        self.english_document_embeddings = self.generate_embeddings(self.documents, self.english_model)
        self.french_document_embeddings = self.generate_embeddings(self.documents, self.french_model)

        self.model_loaded = True  # Mark models as loaded

    def extract_text_from_pdfs(self, folder_path):
        documents = []
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder_path, pdf_file)
            document_data = self.extract_text_from_pdf(pdf_path)
            documents.extend(document_data)
        return documents

    def extract_text_from_pdf(self, pdf_path):
        document_data = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text:
                document_data.append({
                    "pdf_name": os.path.basename(pdf_path),
                    "page_number": page_num + 1,
                    "content": text
                })
        return document_data

    def generate_embeddings(self, documents, model):
        texts = [doc["content"] for doc in documents]
        return model.encode(texts, convert_to_tensor=True)

    def get_language_model(self, query):
        try:
            language = detect(query)
        except Exception as e:
            language = 'en'  # Default to English if detection fails

        if language == 'en':
            return self.english_model, self.english_document_embeddings
        elif language == 'fr':
            return self.french_model, self.french_document_embeddings
        else:
            return self.english_model, self.english_document_embeddings

    def semantic_search(self, query):
        if not self.model_loaded:
            raise Exception("Models are not yet loaded. Please wait and try again.")

        model, document_embeddings = self.get_language_model(query)
        query_embedding = model.encode(query, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(query_embedding, document_embeddings)[0]
        top_results = torch.topk(cosine_scores, k=5)
        results = [
            {
                "pdf_name": self.documents[idx]["pdf_name"],
                "page_number": self.documents[idx]["page_number"],
                "content_snippet": self.documents[idx]["content"][:800],
                "score": score.item()
            }
            for idx, score in zip(top_results.indices, top_results.values)
        ]
        return results