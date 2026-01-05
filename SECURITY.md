# Security Policy

## Supported Versions

| Version               | Supported          |
| --------------------- | ------------------ |
| Latest TinyDB release | :white_check_mark: |
| All prior versions    | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you believe you've found a security vulnerability in TinyDB, please report it by using GitHub's private vulnerability reporting feature.

Please include:

- A clear description of the vulnerability
- A realistic attack scenario demonstrating how untrusted external input leads to the security impact
- Steps to reproduce
- Your assessment of severity and impact

I aim to respond within 7 days and will work with you on a fix and coordinated disclosure on a mutually agreed timeline if the issue is valid.

## Scope: What Constitutes a TinyDB Vulnerability

This security policy applies to the TinyDB core library. Third-party extensions and plugins are not covered by this policy.

For a report to be considered a valid TinyDB vulnerability, it must demonstrate:

1. **A realistic attack chain** where untrusted external data (user input, network data, file contents, etc.) causes unintended security impact through TinyDB's code
2. **TinyDB as the root cause**, not merely a component downstream of an existing application-level vulnerability

### Explicitly Out of Scope

Security reports must demonstrate that TinyDB itself is the source of the vulnerability, not simply present in a vulnerable application.

The following are **not** considered TinyDB vulnerabilities:

- **Passing malicious callables to TinyDB APIs.** TinyDB accepts callables (for queries, serialization, etc.) by design. If an attacker can inject arbitrary Python callables into your application, you already have an arbitrary code execution vulnerability unrelated to TinyDB. This is an application-level concern.

- **Unsafe deserialization in application code.** If your application uses `eval()`, `pickle.loads()`, or similar on untrusted input and passes the result to TinyDB, the vulnerability is in your application's deserialization, not TinyDB.

- **Local file access.** TinyDB reads and writes to local files specified by the application developer. If an attacker has filesystem access or can control file paths, this represents a broader system compromise.

- **Denial of service via large data.** TinyDB is not designed for adversarial multi-tenant environments. Applications should validate data before storage. _However_, DoS issues **may** be considered in-scope if they are caused by TinyDB internals (e.g., algorithmic complexity or pathological performance triggered by small, valid inputs), rather than by unbounded application data.
