## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 16.68s
```
  update_festival_details: 4257.58ms for      2 calls
            compute_angas: 7382.23ms for      1 calls
  get_all_angas_in_period:    3.04ms for   1980 calls
  apply_month_anga_events:    1.04ms for   3960 calls
  _get_relevant_festivals:    0.91ms for   3950 calls
           set_rule_dicts: 1051.20ms for      1 calls
             dump_to_file:  491.52ms for      1 calls
                     find:    3.15ms for    106 calls
  assign_festival_numbers:    2.16ms for      2 calls
assign_festivals_from_rules:    1.12ms for      2 calls
```

## Comment:
