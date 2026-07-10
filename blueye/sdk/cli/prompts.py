"""Interactive prompting seam for the `blueye bundle-model` CLI.

All user questions go through the :class:`Prompter` protocol so the orchestration can
be tested with a fake, and so non-interactive runs (``--yes`` or no TTY) resolve every
question to its default — or fail with a message naming the flag to pass.
"""

from __future__ import annotations

import logging
from typing import Protocol, Sequence

import questionary

from .errors import CliError

logger = logging.getLogger(__name__)


class PromptAborted(Exception):
    """The user cancelled a prompt (Ctrl+C / EOF)."""


class Prompter(Protocol):
    """The questions the CLI commands can ask. Implementations decide how."""

    def select(
        self, question: str, choices: Sequence[str], default: str | None, flag: str
    ) -> str: ...

    def text(self, question: str, default: str, flag: str) -> str: ...

    def confirm(self, question: str, default: bool, flag: str) -> bool: ...

    def path(self, question: str, default: str | None, flag: str) -> str: ...

    def checkbox(self, question: str, choices: Sequence[str], flag: str) -> list[str]: ...


def _require(answer: object) -> object:
    """Translate questionary's None (Ctrl+C) into PromptAborted."""
    if answer is None:
        raise PromptAborted()
    return answer


def _visible_values(inquirer_control) -> list:
    """The selectable values currently shown (respecting the active search filter)."""
    from questionary.prompts.common import Separator

    return [
        choice.value
        for choice in inquirer_control.filtered_choices
        if not isinstance(choice, Separator) and not choice.disabled
    ]


def _toggle_all_visible(inquirer_control) -> None:
    """Select every visible row, or deselect them when all are already selected."""
    visible = _visible_values(inquirer_control)
    if visible and all(value in inquirer_control.selected_options for value in visible):
        for value in visible:
            inquirer_control.selected_options.remove(value)
    else:
        for value in visible:
            if value not in inquirer_control.selected_options:
                inquirer_control.selected_options.append(value)


def _invert_visible(inquirer_control) -> None:
    """Invert the selection of the visible rows, leaving hidden selections intact."""
    for value in _visible_values(inquirer_control):
        if value in inquirer_control.selected_options:
            inquirer_control.selected_options.remove(value)
        else:
            inquirer_control.selected_options.append(value)


def _scope_bulk_bindings_to_filter(question) -> None:
    """Make ctrl-a (toggle all) and ctrl-i/tab (invert) respect the search filter.

    Works around a questionary 2.1.1 bug: with ``use_search_filter=True`` its
    toggle-all/invert handlers iterate every choice instead of the filtered view, so
    filtering and then pressing ctrl-a selected files the user could not even see.
    The original bindings are replaced with ones scoped to `filtered_choices`.
    """
    from prompt_toolkit.keys import Keys
    from questionary.prompts.common import InquirerControl

    application = question.application
    inquirer_control = next(
        control
        for control in application.layout.find_all_controls()
        if isinstance(control, InquirerControl)
    )
    bindings = application.key_bindings
    bindings.remove(Keys.ControlA)
    bindings.remove(Keys.ControlI)

    @bindings.add(Keys.ControlA, eager=True)
    def _toggle_all(_event):
        _toggle_all_visible(inquirer_control)

    @bindings.add(Keys.ControlI, eager=True)
    def _invert(_event):
        _invert_visible(inquirer_control)


class QuestionaryPrompter:
    """Interactive prompts with arrow-key selection and path autocompletion."""

    def select(self, question: str, choices: Sequence[str], default: str | None, flag: str) -> str:
        default_choice = default if default in choices else None
        return str(
            _require(
                questionary.select(
                    question,
                    choices=list(choices),
                    default=default_choice,
                    use_search_filter=True,
                    use_jk_keys=False,
                ).ask()
            )
        )

    def text(self, question: str, default: str, flag: str) -> str:
        return str(_require(questionary.text(question, default=default).ask()))

    def confirm(self, question: str, default: bool, flag: str) -> bool:
        return bool(_require(questionary.confirm(question, default=default).ask()))

    def path(self, question: str, default: str | None, flag: str) -> str:
        return str(_require(questionary.path(question, default=default or "").ask()))

    def checkbox(self, question: str, choices: Sequence[str], flag: str) -> list[str]:
        prompt = questionary.checkbox(
            question,
            choices=list(choices),
            use_search_filter=True,
            use_jk_keys=False,
            # questionary 2.1.1's default instruction wrongly shows <ctrl-a> for
            # both actions when the search filter is on; the real bindings are
            # ctrl-a = toggle all and ctrl-i (tab) = invert.
            instruction=(
                "(use arrow keys to move, <space> to select, <ctrl-a> to toggle "
                "all, <tab> to invert, type to filter)"
            ),
        )
        _scope_bulk_bindings_to_filter(prompt)
        answer = _require(prompt.ask())
        return [str(item) for item in answer]


class NonInteractivePrompter:
    """Prompt resolution for ``--yes`` runs and non-TTY environments.

    Every question resolves to its default. A question without a usable default is a
    hard error that names the command line flag which would have answered it.
    """

    def select(self, question: str, choices: Sequence[str], default: str | None, flag: str) -> str:
        if default is None:
            raise CliError(
                f"Cannot answer '{question}' non-interactively — pass {flag} "
                f"(one of: {', '.join(choices)})."
            )
        return default

    def text(self, question: str, default: str, flag: str) -> str:
        if not default:
            raise CliError(f"Cannot answer '{question}' non-interactively — pass {flag}.")
        return default

    def confirm(self, question: str, default: bool, flag: str) -> bool:
        return default

    def path(self, question: str, default: str | None, flag: str) -> str:
        if not default:
            raise CliError(f"Cannot answer '{question}' non-interactively — pass {flag}.")
        return default

    def checkbox(self, question: str, choices: Sequence[str], flag: str) -> list[str]:
        raise CliError(f"Cannot answer '{question}' non-interactively — pass {flag}.")
