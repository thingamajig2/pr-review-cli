import click
import subprocess
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_git_diff(ref: str = None) -> str:
    """Get git diff from a ref or staging area."""
    if ref:
        result = subprocess.run(
            ["git", "diff", ref],
            capture_output=True,
            text=True,
            check=True
        )
    else:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
    return result.stdout


def review_code(diff: str) -> str:
    """Send diff to Claude for review."""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a code reviewer. Review this diff for:
- Bugs or potential issues
- Performance problems
- Code style/readability
- Security concerns
- Better approaches

Be concise and specific. Format as a bulleted list.

Diff:
```
{diff}
```"""
            }
        ]
    )
    return message.content[0].text


@click.command()
@click.option(
    "--ref",
    default=None,
    help="Git ref to compare against (default: HEAD)"
)
def main(ref):
    """Review code changes with AI."""
    try:
        diff = get_git_diff(ref)
        if not diff.strip():
            click.echo("No changes to review.")
            return

        click.echo("Reviewing code...\n")
        review = review_code(diff)
        click.echo(review)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running git: {e.stderr}", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    main()
