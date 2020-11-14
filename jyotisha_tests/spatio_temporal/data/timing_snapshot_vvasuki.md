## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 14.5s
```
  update_festival_details: 3869.80ms for      2 calls
            compute_angas: 7122.18ms for      1 calls
  get_all_angas_in_period:    2.94ms for   1980 calls
assign_festivals_from_rules:  759.32ms for      2 calls
          assign_festival:    0.00ms for  380016 calls
           set_rule_dicts:  556.29ms for      1 calls
assign_tithi_yoga_nakshatra_fest:    0.02ms for  32124 calls
             dump_to_file:  489.02ms for      1 calls
                     find:    3.13ms for    104 calls
  assign_festival_numbers:    2.00ms for      2 calls
```

## Comment:
