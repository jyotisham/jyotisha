From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

run time: 19s
```
  update_festival_details: 5671.16ms for      2 calls
            compute_angas: 7041.73ms for      1 calls
assign_festivals_from_rules: 3297.53ms for      2 calls
          assign_festival:    0.01ms for  500780 calls
  get_all_angas_in_period:    2.83ms for   1910 calls
                     find:    7.11ms for     89 calls
           set_rule_dicts:  562.79ms for      1 calls
             dump_to_file:  389.41ms for      1 calls
  assign_festival_numbers:    2.21ms for      2 calls
```

## Comment:
Roughly .4 sec