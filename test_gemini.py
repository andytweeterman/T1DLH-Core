import google.generativeai as genai

try:
    print(genai.__version__)
except Exception as e:
    pass

model = genai.GenerativeModel('gemini-2.0-flash', system_instruction="You are a helpful assistant")
print(model)
