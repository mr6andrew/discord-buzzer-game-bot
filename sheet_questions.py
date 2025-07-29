# fetch the google sheet data by making http requests to the sheet's url
import requests
import csv
from io import StringIO


def get_questions_from_sheet(sheet_url=None):
    """
    fetches questions from a google sheet csv link.
    detects whether the sheet is for multiple-choice or written (short answer) questions.
    """
    if not sheet_url:
        return {}

    response = requests.get(sheet_url)
    if response.status_code != 200:
        # something went wrong while fetching the sheet
        return {}

    # convert csv text into rows
    csv_data = response.text.splitlines()
    reader = csv.reader(csv_data)
    header = next(reader)

    is_mc = "answer (magnitude)" not in response.text.lower()

    questions = {}
    for row in reader:
        if not row or not row[0].strip():
            # skip empty rows or rows without a question
            continue

        if is_mc:
            # multiple choice format
            question = row[0].strip()
            choices_raw = row[1:5]
            # i used chr(97 + i) to generate a/b/c/d labels
            choices = [f"{chr(97+i)}. {choice.strip()}" for i,
                       choice in enumerate(choices_raw) if choice.strip()]
            answer = row[5].strip().lower() if len(row) > 5 else ""
            explanation = row[6].strip() if len(row) > 6 else ""
            image_link = row[7].strip() if len(row) > 7 else ""

            if question and choices and answer:
                questions[question] = {
                    "choices": choices,
                    "answer": answer,
                    "explanation": explanation,
                    "image_link": image_link
                }
        else:
            # written format (short/numeric answer)
            question = row[0].strip()
            magnitude = row[1].strip() if len(row) > 1 else ""
            unit = row[2].strip() if len(row) > 2 else ""
            # store both versions of the answer (with and without space)
            answer = f"{magnitude}{unit}".strip()
            answer_with_space = f"{magnitude} {unit}".strip()
            explanation = row[3].strip() if len(row) > 3 else ""
            image_link = row[4].strip() if len(row) > 4 else ""

            if question and answer:
                questions[question] = {
                    "answer": answer,  # store without space
                    "answer_with_space": answer_with_space,  # store with space for display
                    "explanation": explanation,
                    "image_link": image_link
                }

    return questions
