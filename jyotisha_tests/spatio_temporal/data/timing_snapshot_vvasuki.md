## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 14.5s
```
            compute_angas: 7489.28ms for      1 calls
  update_festival_details: 6278.58ms for      1 calls
  get_all_angas_in_period:    2.59ms for   2376 calls
  apply_month_anga_events:    1.80ms for   2376 calls
  _get_relevant_festivals:    1.68ms for   2370 calls
           set_rule_dicts:  669.35ms for      1 calls
             dump_to_file:  549.99ms for      1 calls
                     find:    3.09ms for     94 calls
  assign_festival_numbers:    2.16ms for      1 calls
```

## Comment:
