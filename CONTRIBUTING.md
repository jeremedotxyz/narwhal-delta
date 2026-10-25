# Contributing

1. Start from a reproducible issue or a small, scoped behavior change. Preserve raw inputs and missing-data distinctions.
2. Install Python 3.10+ and the package with `python -m pip install .` in an isolated environment.
3. Run `python -m unittest discover -s tests -v`, `python examples/reproduce.py`, and `node --check src/narwhal_delta/web/app.js`.
4. For a numerical change, add an analytic test with a known result or a discriminating counterexample; document the estimator, assumptions and limits. Avoid tests that only restate implementation.
5. For interface changes, inspect a desktop and narrow phone layout, keyboard paths, import errors, stale controls and export behavior. Include a real screenshot.
6. Update `docs/methods.md`, `docs/data-contracts.md` and `CHANGELOG.md` when a contract changes. Changes to analysis semantics need an intentional version update because the version participates in run identity.
7. Do not add a badge claiming a certification, code coverage percentage, external audit, standard compliance or peer review without a verifiable basis.

The initial repository does not grant an open-source license. Public visibility alone does not supply a license. Resolve licensing with the owner before proposing redistribution terms. Do not add a license on their behalf.
