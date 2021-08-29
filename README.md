# Planny  
Manage your To-Do list via CLI, with integrations.

# TODO
## Integrations
- [x] Beeminder
- [x] Google Calendar
- [ ] Toggle

## New Task
- [ ] input with "m"/TIME creates new event + timer
- [ ] input without "m"/Time creates new task
- [ ] connect timer.timeout to activates GTBee
- [ ] add task to database
- [ ] add Google Calendar integration
- [ ] parse tag of task, if not available then infer if possible
- [ ] input SUCCESS finishes tasks, add it to completed_tasks, stops timer
- [ ] fuzzy search when creating new task from all tasks in database
- [ ] Categorize automatically: E.g. 'mechanics 3.2' Enters automatically to 'mechanics' section  under subsection 'week 3'.

## Task Organization
- [ ] if expression starts with "plan"
## Task Playlist
- [ ] show current event
- [ ] entering "playlist-name" starts that playlist
- [ ] entering "5minutes" when a task is active adds 5 more minutes to current task
- [ ] Calendar Event could be "start Phys-Week3", which means play that playlist
- [ ] Calendar Event could be also "start Phys", which will simply play the topmost playlist 
- [ ] playlists (e.g. Infi-Week3, Infi-Week4) are enumerated, so they have an order
## Google calendar
- [ ] add update to event
- [ ] add delete to event

## Reminders
- [ ] Message contains how much is missing to outperform yesterday / reach completion
## database
- [ ] read about elasticsearch
## iOS
- [ ] read about Swift

## Parsing
- [ ] shorthands:
  - [ ] "g","ig","y","iy" for google, incognito-google, youtube, incognito-youtube
- [ ] detect that 'mechanics' relates to 'physics'
- [ ] 

## Usage
```bee slug value```

```task Mechanics 3.2 [20minutes]``` - adds 'Mechanics 3.2' to Task-Playlist Physics:Mechanics:Week 3, by infering,  and adds suggested time to be 20 minutes, value to be 5$.

``` task summary [-p cat:subcat:subsubcat] [20m] [5$]``` - adds task to specified/infered playlist

``` task summary [-p playlist] [12:00-13:00 [date]]``` - adds task to playlist and creates event at specified time.

``` Mechanics 3.2 20m``` creates task, add it to top of current playlist, (moves current task to second place) and start it immediately (even if current task already runs) for 20 minutes / at specified time.  

``` Mechanics 3.2 [20m]|[12:30-12:50 [Wed]] [-p physics]``` - creates task+event for 'Mechanics 3.2' at specified time. 

``` tasks Mechanics Week 3 ``` stores that playlist name, so now all next entries will be (1) Tasks (2) categorized under that playlist

``` r ``` reset, removes stored settings. 

``` f ``` completes current event, moves to next task on Task-Playlist



``` +5m ``` adds 5 minutes to current event.


### Lists of Tasks

- [ ] Lists of tasks, entering "next" finishes current and moves automatically to next.
- [ ] Recurring Lists - Like Morning
- [ ] ability to enter "Morning" - list of tsts

## Progress
- [ ] expectation to perform more and improve gradually

## Misc

- [ ] if not entered new data - fail, charge. If on List - give task 5 more minutes
- [ ] finish tasks by simply entering next mission/ "finish"/"done"
- [ ] Display celebration when finishing a task
- [ ] Punish if not enough time is traced
- [ ] for each task, track how long it took
- [ ] insert pomo breaks automatically

## Ideas