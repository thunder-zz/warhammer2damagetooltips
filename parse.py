from logger import Logger
from spell_manager import SpellManager
from ability_tooltip_generator import AbilityTooltipGenerator
from structs import XMLFactory, TSVFactory
import inspect
import math

# Debug code for comparing XML & TSV factories
def compare_factories(fac1, fac2):
    assert_factories(fac1.get_projectiles(), fac2.get_projectiles(), "Projectile")
    assert_factories(fac1.get_projectile_explosions(), fac2.get_projectile_explosions(), "Bombardment")
    assert_factories(fac1.get_ability_phases(), fac2.get_ability_phases(), "Ability phase")
    assert_factories(fac1.get_special_unit_abilities(), fac2.get_special_unit_abilities(), "Special unit ability")
    assert_factories(fac1.get_vortexs(), fac2.get_vortexs(), "Vortex")

def assert_factories(fact1, fact2, type_str):
    assert len(fact1) == len(fact2), type_str + " length mismatch."
    for key in fact1:
        assert key in fact2, "Missing " + type_str.lower() +" with key: " + key + " in second factory."
        o1 = fact1[key]
        o2 = fact2[key]
        assert_object(o1, o2)

def assert_object(o1, o2):
    assert o1.__class__.__name__ == o2.__class__.__name__, "Class mismatch"
    o1_items = o1.__dict__.items()
    o2_items = o2.__dict__.items()

    assert len(o1_items) == len(o2_items), "Attribute count mistmatch"
    for attribute, value in o1_items:
        if (isinstance(value, float)):
            assert math.isclose(value, getattr(o2, attribute), rel_tol=1e-2), "Value mismatch for attribute: '{}' o1-val={} o2-val={} o1={} o2={}".format(attribute,value, getattr(o2, attribute), o1, o2)
        else:
            assert value == getattr(o2, attribute), "Value mismatch for attribute: '{}' o1-val={} o2-val={} o1={} o2={}".format(attribute,value, getattr(o2, attribute), o1, o2)


log = Logger("log.txt")

# Use either XML or TSV factory
factory = XMLFactory(log, "xml/projectiles.xml", "xml/projectile_bombardments.xml", "xml/projectiles_explosions.xml", "xml/unit_special_abilities.xml", "xml/battle_vortexs.xml", "xml/special_ability_phases.xml")
#factory2 = TSVFactory(log, "tsv/projectiles.tsv", "tsv/projectile_bombardments.tsv", "tsv/projectiles_explosions.tsv", "tsv/unit_special_abilities.tsv", "tsv/battle_vortexs.tsv", "tsv/special_ability_phases.tsv")
#compare_factories(factory, factory2)


atg = AbilityTooltipGenerator(log)
spell_manager = SpellManager(factory)
spell_manager.generate_tooltips(atg, log)
atg.generate_tsv_files(log)


#atg.test_output_integrity(True, True, True)

