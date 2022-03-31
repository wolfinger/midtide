# midtide
app that books time on your google calendar to go surfing when it's mid tide
  
## optimization parameters
`start time` / `end time` allow customization by day of week, holidays
- `absolute`
- `relative` (to dawn / dusk)
- `mid tide band` how far from mid tide is acceptable if there are calendar conflicts
- `length` how long to shred
  
`wave size` min (max?)  
`swell period` min to max  (e.g., >12s @ pb is closey central)  
`swell diretion` array of directions where it slaps hard  
`wind` max  
`rain` within the past [24/48/72] hours  
`water temp` don't be soft ... more so for wetsuit mapping in the cal event  
`tide behavior` rising, draining, king, slack, etc.  