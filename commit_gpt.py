'''Commit GPT Application

Usage: commit_gpt.py [path]
'''
import os
import sys
import openai

from git.repo import Repo
from dotenv import load_dotenv
from rich.console import Console


def check_environment_variables() -> None:
    '''Check if environment variables are set'''
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")
    if not os.getenv("OPENAI_ORGANIZATION"):
        raise ValueError("OPENAI_ORGANIZATION is not set")
    if not os.getenv("SUMMARY_CONTEXT"):
        raise ValueError("SUMMARY_CONTEXT is not set")
    if not os.getenv("COMMIT_CONTEXT"):
        raise ValueError("COMMIT_CONTEXT is not set")


def connect_to_openai() -> None:
    '''Connect to OpenAI API'''
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.organization = os.getenv("OPENAI_ORGANIZATION")


def clear_screen() -> None:
    '''Clear the screen'''
    os.system('cls' if os.name == 'nt' else 'clear')


def print_to_console(
        output: Console,
        text: str,
        type_of_message: str = '_') -> None:
    '''Print text to console'''
    style = 'normal white'
    match type_of_message:
        case 'info':
            style = 'bold blue'
        case 'success':
            style = 'bold green'
        case 'warning':
            style = 'bold yellow'
        case 'error':
            style = 'bold red'
        case _:
            style = 'default on default'

    output.print(text, style=style)


def get_repo_path_from_argument() -> str:
    '''Get repo path from argument'''
    number_of_arguments = len(sys.argv)

    match number_of_arguments:
        case 2:
            return sys.argv[1]
        case 1:
            return os.path.dirname(os.path.realpath('__file__'))
        case _:
            raise ValueError(
                "Utilisation: python commit_gpt.py [path]"
            )


def get_repo(repo_path: str) -> Repo:
    '''Get repo'''
    return Repo(repo_path)


def get_modified_files(repo: Repo) -> list[str]:
    '''Get modified files
    Args:
        repo (Repo): Git repository
    Returns:
        list[str]: List of modified files

    Check for any modified files in the Git repository by comparing the current state of
    the repository with the HEAD commit. It does this by using the `diff` method of the 
    `index` object of the `repo` object, which returns a list of `DiffIndex` objects 
    representing the changes between the two states. The list comprehension `[item.a_path
    for item in repo.index.diff("HEAD")]` extracts the path of each modified file from the 
    `DiffIndex` objects and stores them in the `modified_files` list.
    '''
    return [item.a_path for item in repo.index.diff("HEAD")]


def stop_if_no_modified_file(console: Console, modified_files: list[str]) -> None:
    '''Check for modified files'''
    if not modified_files:
        print_to_console(
            console,
            '''Aucun fichier modifié n'a été trouvé. 
            Veuillez utiliser git add pour ajouter des fichiers.''',
            'error'
        )
        raise ValueError(
            '''Aucun fichier modifié n'a été trouvé. 
            Veuillez utiliser git add pour ajouter des fichiers.'''
        )


def get_diffs(repo: Repo, modified_files: list[str]) -> list[str]:
    '''Get diffs'''
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
    return diffs


def generate_summary(console: Console, diffs: list[str], context: str) -> str:
    '''Get summary'''
    while True:
        summary_prompt = "\n".join(diffs)
        response_summary = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'system', 'content': context},
                {'role': 'user', 'content': summary_prompt}
            ],
            temperature=0.7,
            max_tokens=100,
        )

        summary_message = response_summary.choices[-1].message.content.strip()

        print_to_console(
            output=console,
            text='Résumé des modifications:',
            type_of_message='success'
        )
        print_to_console(output=console, text=summary_message)

        user_input = input(
            'Le résumé vous convient-il? (o/n) [default: n] ')
        if not user_input:
            user_input = 'n'

        match user_input:
            case 'o':
                return summary_message
            case 'n':
                continue
            case _:
                continue


def generate_commit_message(
        console: Console,
        modified_files: list[str],
        summary_message: str,
        context: str) -> str:
    '''Get commit message'''
    while True:
        commit_prompt = "\n".join(modified_files + [summary_message])
        response_commit = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'system', 'content': context},
                {'role': 'user', 'content': commit_prompt}
            ],
            temperature=0.7,
            max_tokens=100,
        )
        commit_message = response_commit.choices[-1].message.content.strip()

        print_to_console(
            output=console,
            text='Message de commit:',
            type_of_message='success'
        )
        print_to_console(output=console, text=commit_message)

        user_input = input(
            'Le message de commit vous convient-il? (o/n) [default: n] ')
        if not user_input:
            user_input = 'n'

        match user_input:
            case 'o':
                return commit_message
            case 'n':
                continue
            case _:
                continue


def commit_and_push(
        console: Console,
        repo: Repo,
        commit_message: str) -> None:
    '''Commit and push'''
    print_to_console(
        output=console,
        text='Commit en cours...',
        type_of_message='info'
    )
    repo.git.commit(message=commit_message)
    origin = repo.remote(name='origin')
    origin.push()
    print_to_console(
        output=console,
        text='Commit terminé.',
        type_of_message='success'
    )


def main() -> None:
    '''Main function'''
    console = Console()
    clear_screen()

    print_to_console(
        output=console,
        text="Bienvenue dans Commit GPT",
        type_of_message='info'
    )

    load_dotenv()
    check_environment_variables()

    connect_to_openai()

    repo_path = get_repo_path_from_argument()
    repo = get_repo(repo_path=repo_path)

    modified_files = get_modified_files(repo=repo)
    stop_if_no_modified_file(
        console=console,
        modified_files=modified_files
    )

    print_to_console(console, "Fichiers modifiés:", 'info')
    print_to_console(console, '\n'.join(modified_files))

    diffs = get_diffs(repo, modified_files)
    print_to_console(console, "Différences:", 'info')
    print_to_console(console, '\n'.join(diffs))

    summary_message = generate_summary(
        console=console,
        diffs=diffs,
        context=os.getenv("SUMMARY_CONTEXT")
    )
    print_to_console(console, "Résumé des modifications:", 'info')
    print_to_console(console, summary_message)

    commit_message = generate_commit_message(
        console=console,
        modified_files=modified_files,
        summary_message=summary_message,
        context=os.getenv("COMMIT_CONTEXT")
    )
    print_to_console(console, "Message de commit:", 'info')
    print_to_console(console, commit_message)

    commit_and_push(
        console=console,
        repo=repo,
        commit_message=commit_message,
    )


if __name__ == "__main__":
    main()
