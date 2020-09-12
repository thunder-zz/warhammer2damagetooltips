# Total War Warhammer 2: Ability Tooltip Generator

This spaghetti script generates TSV files containing UI tooltips for abilities in Warhammer 2 based on the DB tables:
* unit_special_abilities
* special_ability_phases
* projectiles
* projectile_bombardments
* battle_vortexs

At the moment it works only with XML representation of the tables (it includes localisation unlike TSV) which can be 
extracted with the Assembly Kit and is also provided in this repo.
I am not planning on implementing TSVFactory (which coould be used for autogenerate tooltips for modded spells) but it is included for reference.

Launch the script using ```python parse.py``` (using Python3).
The generated TSV files are formatted to be compatible with the RustedPackFileManager and can be imported as TSV into a packfile.
