## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 19.7s
```
  update_festival_details: 5946.89ms for      2 calls
            compute_angas: 7060.68ms for      1 calls
assign_festivals_from_rules: 3500.58ms for      2 calls
          assign_festival:    0.01ms for  500780 calls
  get_all_angas_in_period:    3.00ms for   1910 calls
           set_rule_dicts:  569.05ms for      1 calls
             dump_to_file:  542.92ms for      1 calls
                  __sub__:    0.01ms for  54956 calls
                     find:    3.14ms for     89 calls
                  __add__:    0.01ms for  49423 calls
                   __eq__:    0.00ms for  111696 calls
  assign_festival_numbers:    2.50ms for      2 calls
                   __gt__:    0.01ms for     10 calls
```

## Comment:
