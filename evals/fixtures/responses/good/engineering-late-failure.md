## Outcome

The implementation is blocked, not complete: the parser change is in `parser.py`, but the final integration test failed after the unit suite succeeded.

## Verification

- All 42 unit tests passed.
- The integration test exited with status 1 because the registry credential was rejected.

## Next action

Renew the registry credential, then rerun the integration test before treating the work as complete.
