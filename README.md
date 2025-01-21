splunk-arcade-mvc
=================

Set an env var `SPLUNK_OBSERVABILITY_ACCESS_TOKEN` with a value of the token when using devspace,
alternatively ensure this is in your values passed to helm when deploying.

Uninstalling helm chart does not clean pvcs or anything the portal spawns, can clean those with
`make clean-pvcs` and `make clean-players` if wanted. Future us can make cron job to prune these
things after some time or something.
