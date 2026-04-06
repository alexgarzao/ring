---
name: sample-command
description: |
  A sample slash command for testing platform transformations.

argument-hint: "[target] [--format=markdown] [--verbose]"
---

# Sample Command

Execute this command to test the Ring installer.

## Usage

```
/ring:sample-command [target] [--format=markdown] [--verbose]
```

## Description

This command demonstrates:
- Command to workflow transformation for Cursor
- Command to prompt transformation for Cline
- Argument parsing and validation

## Steps

1. Parse the provided arguments
2. Validate the target path
3. Process based on format option
4. Output results

## Examples

Basic usage:
```
/ring:sample-command ./src
```

With options:
```
/ring:sample-command ./src --format=json --verbose
```

## Related

- See also: `ring:helper-agent`
- Related skill: `ring:sample-skill`
