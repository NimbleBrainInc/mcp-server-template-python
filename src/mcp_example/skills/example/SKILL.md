---
name: example
description: How to find and read items with the Example server's tools. Use when a request names an item, or asks what items exist.
---

## Tools

| Tool | Use when... |
|------|-------------|
| `list_items` | The request does not name an item id: browse or find items. Each row is a summary with the item's `id` and `uri`. |
| `get_item` | You hold an item id and need the whole item, including its full description. |

## Context Reuse

- `list_items` rows carry `id`. Pass it to `get_item` as `item_id`.
- A row's `description_preview` is cut short. Call `get_item`, or read the row's `uri`, before quoting or summarizing a description.

## Workflows

### Find an item and read it

1. `list_items` (raise `limit`, up to 100, when the item is not on the first page).
2. Pick the row whose `name` matches the request.
3. `get_item` with that row's `id`.

### Handle a failure

A failed call returns an error with a `code`. On `not_found`, list again and pick an id from the
rows. On `bad_input`, fix the argument the message names. Retry only when `retryable` is true.
