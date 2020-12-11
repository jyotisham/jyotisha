## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 22s
```
            compute_angas: 12215.02ms for      1 calls
  get_all_angas_in_period:    4.26ms for   2376 calls
  update_festival_details: 7933.23ms for      1 calls
  apply_month_anga_events:    1.93ms for   2376 calls
  _get_relevant_festivals:    1.81ms for   2370 calls
             dump_to_file:  828.66ms for      1 calls
           set_rule_dicts:  581.73ms for      1 calls
                     find:    4.96ms for     94 calls
  assign_festival_numbers:    3.03ms for      1 calls
```

## Comment:
