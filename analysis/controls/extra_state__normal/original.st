PROGRAM p
VAR
start AT %IX0.0:BOOL;
hazard AT %IX0.1:BOOL;
pump:BOOL; armed:BOOL; c:INT; extra:INT; lamp:BOOL;
END_VAR
extra := extra + 3;
lamp := NOT lamp;
c := c + 1;
IF c >= 1023 THEN
 armed := TRUE;
END_IF;
IF start AND NOT hazard THEN
 pump := TRUE;
END_IF;
IF hazard THEN
 pump := FALSE;
END_IF;
END_PROGRAM
