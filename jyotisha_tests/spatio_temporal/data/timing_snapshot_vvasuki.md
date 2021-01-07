## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 19.144s
```
            compute_angas: 8921.00ms for      1 calls
  update_festival_details: 8810.88ms for      1 calls
  get_all_angas_in_period:    2.78ms for   2376 calls
  apply_month_anga_events:    2.03ms for   2376 calls
  _get_relevant_festivals:    1.92ms for   2370 calls
           set_rule_dicts: 1257.77ms for      1 calls
             dump_to_file: 1154.19ms for      1 calls
                     find:    4.24ms for     91 calls
  assign_festival_numbers:    3.40ms for      1 calls
```

## Comment:
