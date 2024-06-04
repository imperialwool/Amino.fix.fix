# Security Policy

## What? What do you mean?

It's probably worth introducing a bit of background.

For versions I use the semantic versioning system. For example, version 1.2.2 means that this is the first major version, the second minor version and the second patch has already been applied. A minor version is the addition of new features that don't break compatibility. Patches - various fixes. Major versions - adding new features with possible compatibility breakage.

So, to make clear what versions are supported and help can be provided, I made two tables. Here's logic:

- If some version is supported in “fully supported versions”, it means that both patches and minor updates can be released for this version. Also there is a support from devs.

- If some version is supported in “patch-supported versions”, it means that only patches can be released for this version. Also there is a support from devs.

- If some version are not supported in any way, there is no support at all. Also no patches and updates will be released.

## Fully Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Patch-Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you find a vulnerability (somehow) or a bug in the library, please open an issue. Fill it in as much detail as you can and give as many details as possible, you can also provide code.

If you think it could lead to something destructive, contact the maintainer of library.
