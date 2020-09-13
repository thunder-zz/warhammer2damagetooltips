# Total War Warhammer 2: Ability Tooltip Generator

This spaghetti script generates TSV files containing UI tooltips for abilities in Warhammer 2 based on the DB tables:
* unit_special_abilities
* special_ability_phases
* projectiles
* projectile_bombardments
* battle_vortexs

In addition, if you use TSV format you also need ```special_ability_phases__.loc``` which can be extracted from ```text\db\special_ability_phases__.loc``` with Rusted PackFile Manager (RPFM).
Ensure it is named ```special_ability_phases.tsv.loc``` and placed in the tsv folder of the script.

The tables can be imported either as XML files (from Assembly Kit) or TSV (from RPFM) through the XML/TSV factories. 
The order of headers for TSV files doesn't matter. The types for values are automatically identified.
If you want to create tooltips for modded spells but haven't modified all of the tables, create an empty (only containing the first 2 lines - table name and headers) tsv file for the missing tables.
i.e if you are missing ```battle_vortexs``` create the ```battle_vortexs.tsv``` file containing only:
```
battle_vortexs_tables	16
change_max_angle	contact_effect	damage	damage_ap	duration	expansion_speed	goal_radius	infinite_height	move_change_freq	movement_speed	start_radius	vortex_key	ignition_amount	is_magical	composite_scene	detonation_force	launch_source	building_collision	launch_vfx	height_off_ground	delay	num_vortexes	composite_scene_blood	affects_allies	launch_source_offset	composite_scene_group	delay_between_vortexes
```

Launch the script using ```python parse.py``` (using Python3). 
Sample table data from the latest patch (as of 13/09/2020) have been provided in the ```xml``` & ```tsv``` directories. 
Generated files are placed in the ```/out``` directory.
