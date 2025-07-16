# Time Block Entry Format

Time blocks are of the form:

START - END Type: #ProjectCode Description

where:

- START and END are time in the format HH:MM
- The time block has an optional project code. If no project code is provided
  provided, the #General project is used as a default.

## Type codes

T: Task (Focused, deep work on a deliverable)
M: Meeting (Any scheduled call or in-person meeting)
C: Comms (Emails, Slack, Teams, Phone calls that are not scheduled)
A: Admin (Planning, scheduling, expenses, filing)
L: Learning (Reading documentation, taking a course, watching a tutorial)
B: Break (Lunch, coffee, walk, personal time)

## Project codes

#General (default if no project code is provided)
#Managing
#Team

#Project-NAME

where NAME is a name or acrynom for a project. A project here is quite open. It
could map to a work project name or even a large multi-day effort task.
