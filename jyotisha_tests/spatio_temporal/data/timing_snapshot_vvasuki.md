## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 12.73s
```
            compute_angas: 7182.48ms for      1 calls
  get_all_angas_in_period:    2.97ms for   1980 calls
  update_festival_details: 4752.32ms for      1 calls
  apply_month_anga_events:    1.03ms for   2376 calls
  _get_relevant_festivals:    0.92ms for   2370 calls
           set_rule_dicts:  696.00ms for      1 calls
             dump_to_file:  533.55ms for      1 calls
                     find:    3.08ms for     94 calls
  assign_festival_numbers:    2.11ms for      1 calls
```

## Comment:
