'''Commit GPT Application

Usage: commit_gpt.py [path]
'''
import os
import sys
import openai

from git.repo import Repo
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

SUMMARY_CONTEXT = os.getenv("SUMMARY_CONTEXT")
COMMIT_CONTEXT = os.getenv("COMMIT_CONTEXT")

os.system('cls' if os.name == 'nt' else 'clear')

console = Console()

console.print('''[bold cyan]Démarrage de CommitGPT...[/bold cyan]''')

if len(sys.argv) > 1:
    REPO_PATH = sys.argv[1]
else:
    REPO_PATH = os.path.dirname(os.path.realpath(__file__))

repo = Repo(REPO_PATH)

modified_files = [item.a_path for item in repo.index.diff("HEAD")]
if not modified_files:
    console.print(
        '''[bold red]Aucun fichier modifié n'a été trouvé. 
        Veuillez utiliser git add pour ajouter des fichiers.[/bold red]'''
    )
    sys.exit()

diffs = []
for file in modified_files:
    if not os.path.exists(file):
        diff = repo.git.diff("HEAD", file)
        diffs.append(diff)
    else:
        diff_output = repo.git.diff("HEAD", file)
        lines = diff_output.split('\n')
        diffs.append(
            '\n'.join(
                line for line in lines if line.startswith(
                    ('+', '-')
                ) and not line.startswith(
                    ('---', '+++')
                )
            )
        )

console.print('''[bold green]Fichiers modifiés:[/bold green]''')
console.print('\n'.join(modified_files))

while True:
    try:
        SUMMARY_PROMPT = "\n".join(diffs)
        response_summary = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SUMMARY_CONTEXT},
                {"role": "user", "content": SUMMARY_PROMPT},
            ],
            temperature=0.7,
        )
        summary_message = response_summary.choices[-1].message.content.strip()
    except Exception as e:
        error_message = str(e)
        console.print('''[bold red]GPT-3.5 Turbo n'a pas pu générer de résumé.[/bold red]''')
        console.print(error_message)
        summary_message = input("Veuillez entrer un résumé: ")

    console.print('''[bold green]Résumé des modifications:[/bold green]''')
    console.print(summary_message)
    user_input = input("Est-ce que le résumé vous convient? (y) Oui, (r) Regénérer, (c) Choisir le résumé : ")
    if user_input == "n":
        continue
    elif user_input == "c":
        summary_message = input("Veuillez entrer un résumé: ")
        break
    elif user_input == "y":
        break
