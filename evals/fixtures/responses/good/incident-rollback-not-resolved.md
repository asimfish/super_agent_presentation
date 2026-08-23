Blocked: the deployment of the new version remains blocked after an HTTP 401. Rollback succeeded, and user traffic is healthy on the previous version; the new version is not deployed.

A rotated registry credential is the suspected cause, but that cause is unverified. Validate the credential and its access scope, then attempt a safe redeploy with the normal checks before calling the incident resolved.
