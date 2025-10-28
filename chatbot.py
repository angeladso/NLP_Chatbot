import os
import pandas as pd
import numpy as np
from PIL import Image
import google.generativeai as genai

# -------------------------------------
# SET GEMINI API KEY HERE
# -------------------------------------
GEMINI_API_KEY = "AIzaSyDpxKwFfu0TjpVf48ZK9TBncPZNLfCkBDw"
genai.configure(api_key=GEMINI_API_KEY)

# Models
GEN_MODEL = genai.GenerativeModel("models/gemini-2.0-flash-lite")
EMBED_MODEL = "models/text-embedding-004"


class CollegeChatbot:
    def __init__(self, excel_path="data/frcrce_data.xlsx"):
        self.excel_path = excel_path
        self.data = self.load_excel_data()
        self.index = self.build_semantic_index()

    # -------------------------------
    # LOAD EXCEL
    # -------------------------------
    def load_excel_data(self):
        data = {}
        try:
            xls = pd.ExcelFile(self.excel_path)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet).fillna("")
                data[sheet.lower()] = df
            print(f"✅ Loaded {len(data)} sheets from Excel.")
        except Exception as e:
            print("❌ Error loading Excel:", e)
        return data

    # -------------------------------
    # BUILD SEMANTIC INDEX
    # -------------------------------
    def build_semantic_index(self):
        index = []
        try:
            for domain, df in self.data.items():
                for _, row in df.iterrows():
                    text = " ".join(map(str, row.values))
                    embedding_data = genai.embed_content(model=EMBED_MODEL, content=text)
                    embedding = embedding_data["embedding"]
                    index.append({
                        "domain": domain,
                        "text": text,
                        "embedding": embedding
                    })
            print(f"✅ Indexed {len(index)} entries.")
        except Exception as e:
            print("❌ Error building index:", e)
        return index

    # -------------------------------
    # SEMANTIC SEARCH
    # -------------------------------
    def semantic_search(self, query, top_k=5):
        try:
            q_embed = genai.embed_content(model=EMBED_MODEL, content=query)["embedding"]
            scored = []
            for item in self.index:
                score = np.dot(q_embed, item["embedding"]) / (
                    np.linalg.norm(q_embed) * np.linalg.norm(item["embedding"])
                )
                scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [s[1] for s in scored[:top_k]]
        except Exception as e:
            print("❌ Semantic search error:", e)
            return []

    # -------------------------------
    # IMAGE TEXT EXTRACTION
    # -------------------------------
    def extract_text_from_image(self, image_path):
        try:
            img = Image.open(image_path)
            result = GEN_MODEL.generate_content(["Extract all readable text from this image:", img])
            return result.text.strip()
        except Exception as e:
            print("❌ Image text extraction error:", e)
            return "[Image extraction failed — please upload a clearer image.]"

    # -------------------------------
    # GENERATE SMART RESPONSE
    # -------------------------------
    def generate_response(self, query, image_path=None):
        try:
            # If image provided, extract text first
            if image_path:
                extracted_text = self.extract_text_from_image(image_path)
                query = f"{query}\n\nContext from uploaded image:\n{extracted_text}"

            # Search Excel context
            results = self.semantic_search(query)
            if results:
                context = "\n\n".join([f"- ({r['domain']}) {r['text']}" for r in results])
            else:
                context = "No relevant match found in the Excel database."

            # Ask Gemini for smart answer
            prompt = f"""
You are an intelligent FRCRCE campus chatbot.
Your job is to provide **accurate, concise, and student-friendly answers**
based on the Excel knowledge below.
If the question is vague, summarize the most relevant details meaningfully.

Excel Knowledge Context:
{context}

Question:
{query}

Answer clearly:
"""
            response = GEN_MODEL.generate_content(prompt)
            return response.text.strip() if response and response.text else "I'm sorry, I couldn't generate a response."

        except Exception as e:
            return f"⚠️ Error generating response: {e}"
