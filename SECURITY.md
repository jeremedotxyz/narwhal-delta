# Security and data handling

Narwhal Delta runs on loopback `127.0.0.1`; analysis does not upload surveys to a cloud service. Source/method links open GitHub only when selected. Static assets have no remote fonts, analytics or CDN dependencies.

The browser and CLI accept files you select. ZIPs are read in memory, never extracted. Import checks reject traversal, duplicate names, encrypted members and oversized expanded content. JSON and numeric contracts reject non-finite coordinates. The HTTP server checks Host/Origin, accepts JSON mutations only, serves a fixed asset allowlist, and sends a restrictive content security policy. Report labels and annotations are HTML-escaped.

The process is a **single-user local workbench**, not a hardened multi-user service. Do not bind it to a public interface, reverse-proxy it onto the Internet, or treat loopback as access control against another local process. There is no login, encryption-at-rest, tenancy, durable database or formal security audit. Uploaded surveys remain in process memory until replaced or the process exits. Exported bundles contain normalized full point coordinates and inspection notes; handle them as sensitive if your inputs are sensitive.

SHA-256 manifests detect accidental corruption and make exports inspectable. They do not authenticate an author: anyone who can rewrite an archive can recompute its hashes. Pin the software commit separately for reproducibility. No signing keys, passwords or credentials belong in a report or issue.

Report a security concern through an existing private contact channel with the repository owner; do not publish exploitable details or private survey data in a public issue. No dedicated private reporting endpoint or response-time guarantee is asserted.
