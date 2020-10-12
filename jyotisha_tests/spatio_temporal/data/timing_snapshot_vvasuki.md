## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 18.7s
```
  update_festival_details: 5655.74ms for      2 calls
            compute_angas: 6753.27ms for      1 calls
assign_festivals_from_rules: 3285.12ms for      2 calls
          assign_festival:    0.01ms for  500780 calls
  get_all_angas_in_period:    2.87ms for   1910 calls
           set_rule_dicts:  580.83ms for      1 calls
             dump_to_file:  396.87ms for      1 calls
                     find:    2.97ms for     89 calls
  assign_festival_numbers:    2.16ms for      2 calls
```

## Comment:
