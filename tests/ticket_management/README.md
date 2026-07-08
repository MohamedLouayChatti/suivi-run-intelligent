# Ticket Management — Testing Suite

This is the Domain and Application test suite for the `ticket_management`
module, built against the code exactly as delivered (no new business logic
was added).

## Structure

```
tests/
  ticket_management/
    domain/
      factories.py                        # plain factory functions for entities
      conftest.py                         # fixtures wrapping the factories
      test_ticket_creation.py
      test_ticket_status_transitions.py
      test_ticket_assignment.py
      test_ticket_archiving.py
      test_ticket_priority.py
      test_ticket_comments.py
      test_ticket_attachments.py
      test_ticket_transfer_application.py
      test_ticket_mutability_guard.py     # documents a discovered inconsistency (see below)
      test_comment_entity.py
      test_attachment_entity.py
    application/
      fakes.py                            # FakeTicketRepository / FakeUnitOfWork / FakeEventPublisher / FakeTicketReadRepository
      dto_factories.py                    # factory functions for TicketSummaryDTO / TicketDetailDTO
      conftest.py                         # fixtures wiring the fakes
      commands/
        test_create_ticket.py
        test_assign_ticket.py
        test_reassign_ticket.py
        test_change_status.py
        test_change_priority.py
        test_add_comment.py
        test_edit_comment.py
        test_delete_comment.py
        test_add_ticket_attachment.py
        test_delete_ticket_attachment.py
        test_add_comment_attachment.py
        test_delete_comment_attachment.py
        test_archive_and_restore_ticket.py
        test_transfer_application.py
      queries/
        test_get_ticket.py
        test_list_tickets.py
        test_search_tickets.py
```

170 tests total, all passing.

## Running the tests

```
pip install pytest pytest-asyncio
pytest
```

`pyproject.toml` at the repo root configures `asyncio_mode = "auto"`, so
async test functions run without needing `@pytest.mark.asyncio` on every
test. A root `conftest.py` adds the project root to `sys.path` so the
`app.modules.ticket_management...` import paths used throughout the
codebase resolve correctly regardless of the working directory pytest is
invoked from.

## Assumptions made because of missing infrastructure

The zip only contained the Domain and Application layers — no
Infrastructure (SQLAlchemy models, repositories) and no API layer. That's
expected at this stage, but it required a few decisions:

1. **Package layout.** The source imports everything as
   `app.modules.ticket_management.domain...` /
   `...application...`, but the zip's top level was just `domain/` and
   `application/`. I nested them under `app/modules/ticket_management/`
   (adding `__init__.py` files) so the import paths in the actual source
   files work unmodified — no source code was edited to make tests pass.

2. **Fakes instead of real infrastructure.** `TicketRepository`,
   `UnitOfWork`, and `EventPublisher` are abstract base classes with no
   concrete implementation yet. The application tests use hand-written,
   in-memory fakes (`tests/ticket_management/application/fakes.py`) that
   *subclass* those same ABCs rather than being unrelated stand-ins. This
   means if a real interface's method signature changes later, the fakes
   fail to instantiate and the test suite flags the drift immediately.

3. **`UnitOfWork` has no async context manager.** The interface as given
   only exposes `commit()`/`rollback()`, and every handler manages the
   commit/rollback sequence manually. The fake mirrors that exact shape
   rather than assuming a `__aenter__`/`__aexit__` pattern that isn't in
   the interface.

4. **Commit-failure/rollback behavior.** Every handler follows the same
   `try: commit() / except: rollback(); raise` pattern. `FakeUnitOfWork`
   exposes a `fail_commit_with` attribute so tests can make `commit()`
   raise on demand and assert that (a) `rollback()` was called and (b) no
   event was published for a transaction that never committed. This is
   tested on `create_ticket` and `assign_ticket` as representative cases
   rather than duplicated across all 15 handlers, since it exercises the
   exact same three lines of code in every handler — repeating it
   everywhere would inflate the suite without adding meaningfully
   different coverage. If handlers diverge from that pattern in the
   future, this is the assumption to revisit.

5. **Query handlers are read-side pass-throughs, tested as such.**
   `GetTicketHandler`, `ListTicketsHandler`, and `SearchTicketsHandler` all
   depend on a single `TicketReadRepository` interface, which has no
   concrete implementation yet (no SQL, no filtering/search logic — that's
   an Infrastructure-layer concern that doesn't exist in this codebase
   yet). `ListTicketsHandler` and `SearchTicketsHandler` literally do
   nothing but forward the query object to the repository and return its
   result; `GetTicketHandler` adds one thing — translating a missing
   ticket (`None`) into `TicketNotFound`. `FakeTicketReadRepository`
   (added to `fakes.py`, subclassing the real `TicketReadRepository` ABC)
   records exactly what each method received and returns pre-seeded
   results, so the query tests verify orchestration only: the query
   object reaches the repository unchanged, the repository's result comes
   back out unchanged, and `GetTicketHandler`'s not-found translation
   fires correctly. They deliberately don't assert on filtering/search
   *semantics* (e.g. "does `status=OPEN` actually filter the list?"),
   since that behavior isn't implemented anywhere yet — asserting on it
   now would be testing an assumption rather than the code. That
   filtering behavior belongs in the Infrastructure-layer tests once a
   real `TicketReadRepository` implementation exists.

## Design issue discovered: `start_progress` skips the mutability guard

Every other ticket-mutating method (`assign`, `reassign`, `mark_pending`,
`resume`, `resolve`, `close`, `change_priority`, `add_comment`,
`add_attachment`, `edit_comment`, `delete_comment`,
`add_attachment_to_comment`, `delete_attachment_from_comment`,
`transfer_application`) calls `self._ensure_mutable()`, which blocks the
operation on both `CLOSED` and `ARCHIVED` tickets.

`start_progress()` is the exception: it calls `self._transition_to(...)`
directly, skipping `_ensure_mutable()` entirely. `_transition_to` only
blocks `CLOSED` (via its own redundant check), so **an archived ticket can
currently have its status changed to `IN_PROGRESS` via `start_progress`**,
even though every other mutation on that same ticket is correctly
rejected with `TicketArchived`.

This is very likely an oversight rather than an intended exception, since
there's no other archived-ticket-can-still-restart-work-implicitly rule
described anywhere else in the domain. I did not "fix" this in the
tests — per the task's testing philosophy, tests should validate current
behavior, not invent new rules. `test_ticket_mutability_guard.py` pins the
*current* behavior explicitly and documents, in a comment, exactly what
should change if this gets fixed (the assertion would flip from
"succeeds" to `pytest.raises(TicketArchived)`), so this test will fail
loudly — in a good way — the moment someone fixes the underlying method,
prompting an update rather than silently masking the change.

## Other testing notes

- Timestamps in tests use a fixed `BASE_TIME` plus a small
  `a_moment_after()` helper rather than `datetime.now()`, so tests are
  fully deterministic and there's never any ambiguity about whether two
  successive calls happened at the "same" instant.
- Domain tests never construct a `Ticket` via its dataclass constructor
  directly (except the one negative test for `InvalidAssignee`, which
  needs to bypass the type hints to hit that specific guard) — they go
  through `Ticket.create(...)` and the public state-transition methods
  only, since that's the actual contract consumers of this entity rely
  on.
- Application tests assert on *outcomes* (ticket state after the handle
  call, events published, repository/unit-of-work interactions) rather
  than reaching into private handler internals, so they should stay valid
  through a refactor of the handlers' internal structure as long as the
  observable contract (what gets persisted, what gets published, what
  gets raised) doesn't change.
