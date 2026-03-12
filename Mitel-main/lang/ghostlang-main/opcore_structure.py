[CATEGORY][OPERATION][ARGUMENTS]
```

Where:
- CATEGORY: 1-2 character identifier (C=comm, S=system, D=data, etc.)
- OPERATION: 1-3 character operation code
- ARGUMENTS: Variable length, command-specific

Examples:
```
C:SND "ALERT"         # Communication:Send message
S:MOD OFFLINE         # System:Mode change to OFFLINE
D:SET count 5         # Data:Set variable
F:RUN reboot.gfx      # File:Run script
```

For ultra-constrained channels like Morse, these could be further compressed:
```
C1 ALERT              # C1 = Communication:Send
S2 1                  # S2 1 = System:Mode OFFLINE (where 1=OFFLINE)
