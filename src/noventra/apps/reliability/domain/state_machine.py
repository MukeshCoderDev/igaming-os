"""State machine base — declarative transitions with guards + side-effects.

Per ADR-0044 / DEC-0049: django-fsm or justified alternative. Phase 8
implements a lightweight base (no external dep); Phase 9 may adopt
django-fsm if needed.
"""

from __future__ import annotations

import functools
from typing import Callable


class TransitionError(Exception):
    """Raised when an invalid transition is attempted."""


def transition(
    *,
    source: str,
    target: str,
    guard: Callable[..., bool] | None = None,
):
    """Decorator: declare a state transition.

    Per ADR-0044: declarative transitions; guard pattern; side-effect hooks.
    """

    def decorator(func: Callable) -> Callable:
        transitions = getattr(func, "_transitions", ())
        original_func = getattr(func, "_transition_func", func)
        declared_transitions = (*transitions, (source, target, guard))

        @functools.wraps(original_func)
        def wrapper(self, *args, **kwargs):
            current = self.state
            selected = next(
                (item for item in declared_transitions if item[0] == current),
                None,
            )
            if selected is None:
                expected = ", ".join(f"'{item[0]}'" for item in declared_transitions)
                raise TransitionError(
                    f"Invalid transition: {func.__name__} from state '{current}' "
                    f"(expected one of: {expected})"
                )
            transition_source, transition_target, transition_guard = selected
            if transition_guard is not None and not transition_guard(self, *args, **kwargs):
                raise TransitionError(
                    f"Guard failed for transition {func.__name__} from "
                    f"'{transition_source}' to '{transition_target}'"
                )
            # Side-effect hook: before transition.
            if hasattr(self, "_before_transition"):
                self._before_transition(func.__name__, transition_source, transition_target)

            result = original_func(self, *args, **kwargs)
            self.state = transition_target

            # Side-effect hook: after transition (emit outbox + audit).
            if hasattr(self, "_after_transition"):
                self._after_transition(func.__name__, transition_source, transition_target)

            return result

        wrapper._transition_func = original_func
        wrapper._transitions = declared_transitions
        wrapper._transition_source = source
        wrapper._transition_target = target
        return wrapper

    return decorator


class StateMachineMixin:
    """Mixin for aggregates with state machine transitions.

    Per ADR-0044: optimistic locking (version field); every transition audited.
    """

    state: str = ""
    version: int = 0

    def _before_transition(self, name: str, source: str, target: str) -> None:
        """Override: side-effect before transition."""
        pass

    def _after_transition(self, name: str, source: str, target: str) -> None:
        """Override: side-effect after transition (emit outbox + audit)."""
        pass

    def save(self, *args, **kwargs) -> None:
        """Save with optimistic locking."""
        # Phase 8 stub: real optimistic locking requires a version field
        # in the ORM + SELECT ... FOR UPDATE. Phase 9 implements.
        self.version += 1
