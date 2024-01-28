import os
from pdfminer.high_level import extract_text #consider replaceing it with pdfminer.six
import spacy

# Load the spaCy model
nlp = spacy.load('en_core_web_lg')

# Define the directory path
dir_path = r"C:\Users\philippe\Documents\pdf to txt files"

# Loop through every file in the directory
for filename in os.listdir(dir_path):
    # Check if the file is a PDF
    if filename.endswith("ll.pdf"):
        # Create a text file name by replacing .pdf with .txt
        text_filename = filename.replace(".pdf", ".txt")

        # Extract the text from the PDF
        text = extract_text(os.path.join(dir_path, filename))

        # Split the text into chunks of 500,000 characters each
        chunks = [text[i:i+500000] for i in range(0, len(text), 500000)]

        # Process each chunk with spaCy and combine the results
        sentences = []
        for chunk in chunks:
            doc = nlp(chunk)
            chunk_sentences = [sent.text for sent in doc.sents]
            sentences.extend(chunk_sentences)

        # Join the sentences back into a single text
        text = ' '.join(sentences)

        # Open the text file in write mode
        with open(os.path.join(dir_path, text_filename), 'w', encoding='utf-8') as text_file:
            # Write the text to the text file
            text_file.write(text)
