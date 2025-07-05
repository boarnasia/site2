import google.generativeai as genai
import os


def get_list():
    API_KEY = os.environ.get("$GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    models = genai.list_models()
    return models


def main():
    models = get_list()
    for model in models:
        print(model.name)


if __name__ == "__main__":
    main()
