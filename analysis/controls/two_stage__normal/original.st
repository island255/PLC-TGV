PROGRAM p
VAR
start AT %IX0.0:BOOL;
hazard AT %IX0.1:BOOL;
pump:BOOL; armed:BOOL; c:INT; d:INT; latch:BOOL;
END_VAR
c := c + 1;
IF c >= 127 THEN
 latch := TRUE;
END_IF;
IF latch THEN
 d := d + 1;
END_IF;
IF d >= 257 THEN
 armed := TRUE;
END_IF;
IF start AND NOT hazard THEN
 pump := TRUE;
END_IF;
IF hazard THEN
 pump := FALSE;
END_IF;
END_PROGRAM
