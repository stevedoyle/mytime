# Example Files

This directory contains example daily note files demonstrating both time tracking formats supported by the mytime tools:

## Hierarchical Time Format (mytime.py default)

Files like `2023-10-16.md` use the format:
```
Time.Category.Name: hours
```

Examples:
- `Time.Proj.WebApp: 4.5`
- `Time.Area.Managing: 2`
- `Time.Focus.Deep: 6`

## Time Block Format (--tasks option)

Files like `2024-08-15.md` through `2024-08-20.md` use the format:
```
## Time

HH:MM - HH:MM Type: #ProjectCode Description
```

Examples:
- `09:00 - 11:00 T: #Project-WebApp Frontend development`
- `13:00 - 14:30 M: #Team Sprint planning meeting`
- `15:15 - 17:00 C: #Client Requirements discussion`

### Type Codes

- **T**: Task (development, coding, analysis)
- **M**: Meeting (team meetings, calls)
- **C**: Communication (email, slack, client calls)
- **A**: Administrative (reports, planning, documentation)
- **L**: Learning (training, reading, courses)
- **B**: Break (lunch, coffee breaks)

### Project Codes

- `#Project-WebApp` → Groups under "WebApp"
- `#Project-API` → Groups under "API"
- `#Project-Mobile` → Groups under "Mobile"
- `#Team` → Groups under "Team"
- `#Client` → Groups under "Client"
- `#Training` → Groups under "Training"
- `#General` → Default if no project code specified

## Usage Examples

### Analyze hierarchical time entries
```bash
# Traditional time summary
mytime --path examples --thisweek

# Brief focus summary
mytime --path examples --brief --thisweek
```

### Analyze time block entries with --tasks
```bash
# Show tasks grouped by project for specific date
mytime --tasks --path examples --from 2024-08-15 --to 2024-08-15

# Show all tasks for the week
mytime --tasks --path examples --from 2024-08-15 --to 2024-08-20

# Export to TSV format
mytime --tasks --tsv --path examples --from 2024-08-15 --to 2024-08-20
```

### Extract and aggregate notes with --notes
```bash
# Show notes from today
mytime --notes --path examples --today

# Show notes from a specific date range in reverse chronological order
mytime --notes --path examples --from 2024-08-20 --to 2024-08-22

# Show notes from this week
mytime --notes --path examples --thisweek
```
