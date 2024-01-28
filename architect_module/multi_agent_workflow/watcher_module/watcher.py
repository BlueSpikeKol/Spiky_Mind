from transformers import BertTokenizer, BertForSequenceClassification
import torch

# Step 3: Load Pre-trained BERT Model and Tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Step 4: Preprocess Text
input_text = "Renewable energy is important for sustainability but has challenges."
tokens = tokenizer(input_text, padding=True, truncation=True, return_tensors="pt")

# Step 5: Make Predictions
with torch.no_grad():
    outputs = model(**tokens)
    logits = outputs.logits

# Step 6: Extract Key Ideas
probabilities = torch.softmax(logits, dim=1)
predicted_label = torch.argmax(probabilities, dim=1).item()

print(f"Predicted label: {predicted_label}")
