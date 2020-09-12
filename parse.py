from logger import Logger
from spell_manager import SpellManager
from ability_tooltip_generator import AbilityTooltipGenerator
from structs import XMLFactory

log = Logger("log.txt")
xml_fact = XMLFactory(log, "projectiles.xml", "projectile_bombardments.xml", "projectiles_explosions.xml", "unit_special_abilities.xml", "battle_vortexs.xml", "special_ability_phases.xml")
atg = AbilityTooltipGenerator(log)
spell_manager = SpellManager(xml_fact)
spell_manager.generate_tooltips(atg, log)
atg.generate_tsv_files(log)
#atg.test_output_integrity(True, True, True)