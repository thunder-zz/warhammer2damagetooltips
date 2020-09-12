import xml.etree.ElementTree as ET
from structs import Vortex, Bombardment, Projectile, ProjectileExplosion, SpecialUnitAbility, AbilityPhase


def create_damage_string(dmg, dmgap):
    if dmg <= 0 and dmgap <= 0: return False
    damageTxt = ""
    if(dmg > 0): damageTxt += str(dmg) + " damage"
    if(dmgap > 0):
        if(dmg > 0): damageTxt += " & "
        damageTxt += str(dmgap) + " AP"
    return damageTxt

class SpellManager:
    def __init__(self, ability_factory):
        self.bombardments = ability_factory.get_bombardments()
        self.projectiles = ability_factory.get_projectiles()
        self.projectile_explosions = ability_factory.get_projectile_explosions()
        self.special_unit_abilities = ability_factory.get_special_unit_abilities()
        self.vortexes = ability_factory.get_vortexs()
        self.ability_phases = ability_factory.get_ability_phases()

    def generate_tooltips(self, atg, log):
        log.set_active_class("ProjectileManager")
        # All projectiles must contain any of the words to be included.
        # Ensures that no generic projectiles like arrows have tooltip generation
        projectile_ability_keywords = ["spell", "main_character_abilities", "weapon_abilities", "lord_abilities", "unit_abilities", "army_abilities", "passive"]
        
        # Initial setup
        # Adds damage over time tooltips to spells.
        for ability_phase in self.ability_phases.values():
            damage_txt = ability_phase.get_damage_txt()
            # Only interested in damaging spells
            if damage_txt != False:
                atg.add_phase_tooltip(ability_phase.key, ability_phase.get_damage_txt())

        # Add main damage tooltips to all vortexes
        for vortex in self.vortexes.values():
            atg.add_damage_tooltip(vortex.key, vortex.get_damage_txt())
            if(vortex.start_radius == vortex.goal_radius): atg.add_equal_radius_tooltip(vortex.key, vortex.get_equal_radius_txt())
            elif(vortex.expansion_speed > 0):
                atg.add_expanding_radius_tooltip(vortex.key, vortex.get_expanding_radius_txt())


        # Tooltip generation of projectiles & bombardment spells
        for projectile in self.projectiles.values():
            used_in_bombardments = projectile.is_used_in_bombardment(self.bombardments)
            detonation = projectile.get_projectile_explosion_ref()
            # Create detonation damage tooltip if the projectile has a projectile explosion
            detonation_loc = None
            if detonation != None:
                    detonation_loc = detonation.get_detonation_string()

            if len(used_in_bombardments) > 0:
                # part of at least one bombardment spell
                log.debug("Projectile {key} is a part of bombardment spells: {bspells}".format(key=projectile.key, bspells=str(used_in_bombardments)))
                for bombardment in used_in_bombardments:
                    # Add damage (and detonation if applicable) tooltips for all bombardments that use this projectile
                    localisation = bombardment.get_bombardment_string(projectile)
                    if(localisation != False and not atg.contains_damage_tooltip(bombardment.key)):
                        atg.add_damage_tooltip(bombardment.key, localisation)
                    if detonation_loc != None and not atg.contains_detonation_tooltip(bombardment.key):
                        atg.add_detonation_damage_tooltip_with_local(bombardment.key, detonation_loc)
            else:
                # Magic missile or regular projectile (e.g. arrow) if not used by bombardment
                log.debug("Projectile {key} is a magic missile or projectile".format(key=projectile.key))
                
                keyword = ""
                # Check if the projectile is not generic (e.g. an arrow)
                if not any(keyword in projectile.key for keyword in projectile_ability_keywords): continue

                damage_txt = projectile.get_damage_txt()
                if(damage_txt != False):
                    atg.add_damage_tooltip(projectile.key, damage_txt)
                if detonation_loc != None:
                    atg.add_detonation_damage_tooltip_with_local(projectile.key, detonation_loc)
                if projectile.bonus_v_large > 0:
                    atg.add_bonus_v_large_tooltip(projectile.key, str(projectile.bonus_v_large))
                if projectile.contact_stat_effect != None:
                    contact_effect = self.ability_phases.get(projectile.contact_stat_effect)
                    contact_effect_damage = contact_effect.get_damage_txt()
                    if contact_effect_damage != False:
                        atg.add_on_contact_tooltip(projectile.key, "On Projectile Contact: " + contact_effect_damage[1] + " " + contact_effect_damage[0])

        # Add unit and lord abilites. Most of them are reskins of already added abilities but they still need their own tooltips.
        # If it references a vortex/bombardment/project that has tooltips then all tooltips will be copied over.
        for unit_ability in self.special_unit_abilities.values():
            if unit_ability.wind_up_time == 0 and not unit_ability.is_passive:
                atg.add_wind_up_time_tooltip(unit_ability.key, "Cast time: instant")
            elif unit_ability.wind_up_time > 0 and not unit_ability.is_passive:
                time = unit_ability.wind_up_time if not unit_ability.wind_up_time.is_integer() else int(unit_ability.wind_up_time)
                secondStr = " second" if time == 1 else " seconds"
                atg.add_wind_up_time_tooltip(unit_ability.key, "Cast time: " +str(time) +secondStr)

            if not unit_ability.is_damaging_ability(): 
                log.debug("Skipping " + str(unit_ability) + " because it is not damaging.")
                continue

            (unit_ability_already_added, tooltips) = atg.contains_key(unit_ability.key)
            if unit_ability_already_added: 
                log.debug("Unit ability: {key} already added.".format(key=unit_ability.key))
                log.debug("Tooltips: " + str(tooltips))
                continue

            # Check if ability references a vortex spell we already made tooltips for.
            if unit_ability.used_vortex_key != None:
                (ability_already_added, tooltips) = atg.contains_key(unit_ability.key)
                if ability_already_added:
                    for tooltip in tooltips:
                        self.copy_tooltips(unit_ability.key, tooltip, atg)
                else:
                    log.debug("Need to add new vortex ability: " + unit_ability.key +" that maps to " + unit_ability.used_vortex_key)
                    (contains_vortex, tooltips) = atg.contains_key(unit_ability.used_vortex_key)
                    assert contains_vortex == True, "All vortex spells should be already loaded as they are all decleared in only one file"
                    for tooltip in tooltips:
                        self.copy_tooltips(unit_ability.key, tooltip, atg)

            # Check if ability references a bombardment spell we already made tooltips for.
            elif unit_ability.used_bombardment_key != None:
                (ability_already_added, tooltips) = atg.contains_key(unit_ability.key)
                if ability_already_added:
                    for tooltip in tooltips:
                        self.copy_tooltips(unit_ability.key, tooltip, atg)
                else:
                    log.debug("Need to add new bombardmant ability: " +unit_ability.key +" that maps to " + unit_ability.used_bombardment_key)
                    (contains_bombardment_spell, tooltips) = atg.contains_key(unit_ability.used_bombardment_key)
                    if not contains_bombardment_spell: 
                        log.debug("Need to create new bombardment spell in atg: "+unit_ability.used_bombardment_key)
                        bombardment = self.bombardments[unit_ability.used_bombardment_key]
                        projectile = bombardment.get_projectile(self.projectiles)
                        detonation = projectile.get_projectile_explosion_ref()
                        damage_txt = bombardment.get_bombardment_string(projectile)

                        atg.add_tooltips(unit_ability,  detonation, damage_txt, log)
                        atg.add_tooltips(bombardment,  detonation, damage_txt, log)
                    else:
                        log.debug("Already have bombardment spell in atg: "+unit_ability.used_bombardment_key)
                        for tooltip in tooltips:
                            self.copy_tooltips(unit_ability.key, tooltip, atg)
            # Check if ability references a projectile spell we already made tooltips for.
            elif unit_ability.used_projectile_key != None:
                (ability_already_added, tooltips) = atg.contains_key(unit_ability.key)
                if ability_already_added:
                    for tooltip in tooltips:
                        self.copy_tooltips(unit_ability.key, tooltip, atg)
                else:
                    #print("Need to add new projectile: " +unit_ability.key +" that maps to " + unit_ability.used_projectile_key)
                    log.debug("Need to add new projectile: " +unit_ability.key +" that maps to " + unit_ability.used_projectile_key)
                    (contains_projectile, tooltips) = atg.contains_key(unit_ability.used_projectile_key)
                    if not contains_projectile:
                        log.debug("Need to create new projectile in atg: " +unit_ability.used_projectile_key)
                        projectile = self.projectiles[unit_ability.used_projectile_key]

                        detonation = projectile.get_projectile_explosion_ref()
                        damageTxt = projectile.get_damage_txt()

                        atg.add_tooltips(projectile, detonation, damageTxt, log)
                        atg.add_tooltips(unit_ability, detonation, damageTxt, log)
                        
                    else:
                        for tooltip in tooltips:
                            self.copy_tooltips(unit_ability.key, tooltip, atg)

        log.reset_active_class()
    
    def copy_tooltips(self, unit_ability_key, tooltip, atg):
        if tooltip["tag"] == atg.TAG_DAMAGE_TOOLTIP:
            atg.add_damage_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_DETONATION_DAMAGE_TOOLTIP:
            atg.add_detonation_damage_tooltip_with_local(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_BONUS_V_LARGE:
            atg.add_bonus_v_large_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_PHASE_TOOLTIP:
            atg.add_phase_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_EQUAL_RADIUS:
            atg.add_equal_radius_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_EXPANDING_RADIUS:
            atg.add_expanding_radius_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_WIND_UP_TINE:
            atg.add_wind_up_time_tooltip(unit_ability_key, tooltip["localisation"])
        elif tooltip["tag"] == atg.TAG_ON_CONTACT:
            atg.add_on_contact_tooltip(unit_ability_key, tooltip["localisation"])
        else:
            assert False, "Unkown tooltip tag: " + tooltip["tag"]
