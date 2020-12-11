from logger import Logger
from spell_manager import SpellManager
from ability_tooltip_generator import AbilityTooltipGenerator
from structs import XMLFactory, TSVFactory, FactoryBuilder


log = Logger("log.txt")
"""
# Create tooltips for only vortex spells from tsv files
factory = (FactoryBuilder()
            .with_vortex("tsv/battle_vortexs.tsv")
            .build(log, FactoryBuilder.TSV))

atg = AbilityTooltipGenerator(log)
spell_manager = SpellManager(factory)
spell_manager.generate_tooltips(atg, log)
atg.generate_tsv_files(log)
"""

# Use either XML or TSV factory
factory = XMLFactory(log, "xml/projectiles.xml", "xml/projectile_bombardments.xml", "xml/projectiles_explosions.xml", "xml/unit_special_abilities.xml", "xml/battle_vortexs.xml", "xml/special_ability_phases.xml")
#factory2 = TSVFactory(log, "tsv/projectiles.tsv", "tsv/projectile_bombardments.tsv", "tsv/projectiles_explosions.tsv", "tsv/unit_special_abilities.tsv", "tsv/battle_vortexs.tsv", "tsv/special_ability_phases.tsv")

atg = AbilityTooltipGenerator(log)
spell_manager = SpellManager(factory)
spell_manager.generate_tooltips(atg, log)
atg.generate_tsv_files(log)


#atg.test_loc_integrity()
