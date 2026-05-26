from __future__ import annotations

import typer

from easy_terminal import messages
from easy_terminal.errors import ResolveError
from easy_terminal.executor import ExecutionError, execute
from easy_terminal.history import save_history
from easy_terminal.parser import parse_input
from easy_terminal.resolver import resolve
from easy_terminal.risk import DANGEROUS

app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(args: list[str] = typer.Argument(None)) -> None:
    args = args or []
    parsed = parse_input(args)
    if not parsed:
        typer.echo(messages.NOT_A_COMMAND)
        raise typer.Exit(2)

    try:
        resolution = resolve(parsed)
    except ResolveError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc

    if resolution.risk == DANGEROUS:
        typer.echo("that command is dangerous, are you sure you want to run it? (y/n)")
        raise typer.Exit(1)

    if resolution.commands:
        try:
            execute(resolution)
        except ExecutionError as exc:
            typer.echo(str(exc))
            raise typer.Exit(1) from exc

        save_history(
            input_text="easy " + " ".join(args),
            commands=resolution.commands,
            risk=resolution.risk,
        )
    typer.echo(resolution.message)


if __name__ == "__main__":
    app()
