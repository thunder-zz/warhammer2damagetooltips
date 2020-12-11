from abc import ABC, abstractclassmethod
import xml.etree.ElementTree as ET
import os


def create_damage_string(dmg, dmgap, is_fire_damage, is_magical_damage):
    if dmg <= 0 and dmgap <= 0: return False
    magic_icon = "[[img:icon_dmg_flaming]][[/img]]" if is_fire_damage else "[[img:icon_dmg_magical]][[/img]]" if is_magical_damage else " non magical"
    damageTxt = ""
    if(dmg > 0): damageTxt += str(dmg) + magic_icon +" damage"
    if(dmgap > 0):
        if(dmg > 0): damageTxt += " and "
        damageTxt += str(dmgap) +"[[img:icon_ap]][[/img]]"
    return damageTxt

class FactoryBuilder:
    TSV = 1
    XML = 2

    def __init__(self):
        self.projectiles_path = None
        self.projectile_bombardments_path = None
        self.projectile_explosions_path = None
        self.unit_special_abilities_path = None
        self.vortex_path = None
        self.special_ability_phases_path = None

    def with_projectiles(self, path):
        self.projectiles_path = path
        return self

    def with_bombardments(self, path):
        self.projectile_bombardments = path
        return self

    def with_projectile_explosion(self, path):
        self.projectile_explosions_path = path
        return self

    def with_unit_special_abilities(self, path):
        self.unit_special_abilities_path = path
        return self

    def with_vortex(self, path):
        self.vortex_path = path
        return self

    def with_ability_phase(self, path):
        self.special_ability_phases_path = path
        return self

    def build(self, log, format):
        if format == self.TSV:
            return TSVFactory(log, self.projectiles_path, self.projectile_bombardments_path, self.projectile_explosions_path,
                self.unit_special_abilities_path, self.vortex_path, self.special_ability_phases_path)

        elif format == self.XML:
            return XMLFactory(log, self.projectiles_path, self.projectile_bombardments_path, self.projectile_explosions_path,
                self.unit_special_abilities_path, self.vortex_path, self.special_ability_phases_path)
        else:
            raise Exception("Invalid format provided. Use FactoryBuilder.XML or FactoryBuilder.TSV")
            

    pass

class AbstractFactory(ABC):
    def __init__(self, logger):
        self.bombardments = {}
        self.projectiles = {}
        self.projectile_explosions = {}
        self.special_unit_abilities = {}
        self.vortexes = {}
        self.ability_phases = {}
        self.log = logger
    
    def get_bombardments(self):           return self.bombardments
    def get_projectiles(self):            return self.projectiles
    def get_projectile_explosions(self):  return self.projectile_explosions
    def get_special_unit_abilities(self): return self.special_unit_abilities
    def get_vortexs(self):                return self.vortexes
    def get_ability_phases(self):         return self.ability_phases

    @abstractclassmethod
    def create_ability_phase(self, source): return
    @abstractclassmethod
    def create_vortex(self, source): return
    @abstractclassmethod
    def create_special_unit_ability(self, source): return
    @abstractclassmethod
    def create_projectile_explosion(self, source): return
    @abstractclassmethod
    def create_projectile(self, source): return
    @abstractclassmethod
    def create_bombardment(self, source): return

# Generate structs based on XML files provided by the assembly kit.
class XMLFactory(AbstractFactory):
    def __init__(self, logger, projectiles_xml_path, bombardment_xml_path, projectile_explosions_xml_path, unit_special_abilities_xml_path, vortex_xml_path, phases_xml_path):
        super(XMLFactory, self).__init__(logger)
        self.log.set_active_class("XMLFactory")

        if phases_xml_path:                 self._parse_ability_phases(ET.parse(phases_xml_path).getroot())
        if vortex_xml_path:                 self._parse_vortexs(ET.parse(vortex_xml_path).getroot())
        if projectile_explosions_xml_path:  self._parse_explosions(ET.parse(projectile_explosions_xml_path).getroot())
        if projectiles_xml_path:            self._parse_projectiles(ET.parse(projectiles_xml_path).getroot())
        if bombardment_xml_path:            self._parse_bombardments(ET.parse(bombardment_xml_path).getroot())
        if unit_special_abilities_xml_path: self._parse_unit_abilities(ET.parse(unit_special_abilities_xml_path).getroot())

        self.log.reset_active_class()
    # Parse functions

    def _parse_ability_phases(self, root):
        for ability_phase in root.findall("special_ability_phases"):
            c_ability_phase = self.create_ability_phase(ability_phase)
            self.ability_phases[c_ability_phase.key] = c_ability_phase
            self.log.debug("Adding ability phase: " +str(c_ability_phase))

    def _parse_vortexs(self, root):
        for vortex in root.findall("battle_vortexs"):
            c_vortex = self.create_vortex(vortex)
            self.vortexes[c_vortex.key] = c_vortex
            self.log.debug("Adding vortex: " +str(c_vortex))

    def _parse_explosions(self, root):
        for explosion in root.findall("projectiles_explosions"):
            c_explosion = self.create_projectile_explosion(explosion)
            if c_explosion.detonation_damage > 0 or c_explosion.detonation_damage_ap > 0:
                self.log.debug("Adding explosion: " + str(c_explosion))
                self.projectile_explosions[c_explosion.key] = c_explosion

    def _parse_projectiles(self, root):
        for projectile in root.findall("projectiles"):
            c_projectile = self.create_projectile(projectile)
            projectile_explosion = c_projectile.get_projectile_explosion_if_exists(self.projectile_explosions)
            if projectile_explosion != None: 
                c_projectile.set_projectile_explosion_ref(projectile_explosion)
            self.log.debug("Adding projectile: " + str(c_projectile))
            self.projectiles[c_projectile.key] = c_projectile

    def _parse_bombardments(self, root):
        for bombardment in root.findall("projectile_bombardments"):
            c_bombardment = self.create_bombardment(bombardment)
            self.bombardments[c_bombardment.key] = c_bombardment

    def _parse_unit_abilities(self, root):
        for unit_ability in root.findall("unit_special_abilities"):
            c_unit_ability = self.create_special_unit_ability(unit_ability)
            self.log.debug("Adding unit ability: " + str(c_unit_ability))
            self.special_unit_abilities[c_unit_ability.key] = c_unit_ability

    # Object constructors

    def create_ability_phase(self, xml_element):
        key                  = xml_element.find("id").text
        dmg                  = int(xml_element.find("damage_amount").text)
        dmg_chance           = float(xml_element.find("damage_chance").text)
        duration             = float(xml_element.find("duration").text)
        frequency            = float(xml_element.find("hp_change_frequency").text)
        onscreen_name        = xml_element.find("onscreen_name").text or ""
        max_damaged_entities = int(xml_element.find("max_damaged_entities").text)
        
        return AbilityPhase(key, dmg, dmg_chance, duration, frequency, max_damaged_entities, onscreen_name)

    def create_vortex(self, xml_element):
        key             = xml_element.find("vortex_key").text
        dmg             = int(xml_element.find("damage").text)
        dmgap           = int(xml_element.find("damage_ap").text)
        is_fire_damage  = int(xml_element.find("ignition_amount").text) == 1
        is_magical      = int(xml_element.find("is_magical").text) == 1
        goal_radius     = float(xml_element.find("goal_radius").text)
        start_radius    = float(xml_element.find("start_radius").text)
        movement_speed  = float(xml_element.find("movement_speed").text)
        expansion_speed = float(xml_element.find("expansion_speed").text)
        contact_effect  = xml_element.find("contact_effect").text

        return Vortex(key, dmg, dmgap, is_fire_damage, is_magical, goal_radius, start_radius, movement_speed, expansion_speed, None, contact_effect)

    def create_special_unit_ability(self, xml_element):
        key                  = xml_element.find("key").text
        used_projectile_key  = xml_element.find("activated_projectile").text
        used_vortex_key      = xml_element.find("vortex").text
        used_bombardment_key = xml_element.find("bombardment").text
        wind_up_time         = float(xml_element.find("wind_up_time").text)
        is_passive           = (int)(xml_element.find("passive").text) == 1

        return SpecialUnitAbility(key, used_projectile_key, used_vortex_key, used_bombardment_key, wind_up_time, is_passive)

    def create_projectile_explosion(self, xml_element):
        key              = xml_element.find("key").text
        detonation_dmg   = int(xml_element.find("detonation_damage").text)
        detonation_dmgap = int(xml_element.find("detonation_damage_ap").text)
        magical          = int(xml_element.find("is_magical").text) == 1
        
        return ProjectileExplosion(key, detonation_dmg, detonation_dmgap, magical)

    def create_projectile(self, xml_element):
        key                 = xml_element.find("key").text
        dmg                 = int(xml_element.find("damage").text)
        dmgap               = int(xml_element.find("ap_damage").text)
        bonus_v_large       = int(xml_element.find("bonus_v_large").text)
        bonus_v_infantry    = int(xml_element.find("bonus_v_infantry").text)
        is_fire_damage      = int(xml_element.find("ignition_amount").text) > 0
        is_magical          = int(xml_element.find("is_magical").text) == 1
        projectile_number   = int(xml_element.find("projectile_number").text)
        voley               = int(xml_element.find("shots_per_volley").text)
        explosion_type      = xml_element.find("explosion_type").text
        contact_stat_effect = xml_element.find("contact_stat_effect").text

        return Projectile(key, dmg, dmgap, bonus_v_large, bonus_v_infantry, is_fire_damage, is_magical, projectile_number, voley, explosion_type, None, contact_stat_effect)

    def create_bombardment(self, xml_element):
        key                 = xml_element.find("bombardment_key").text
        num_projectiles     = int(xml_element.find("num_projectiles").text)
        projectile_type_key = xml_element.find("projectile_type").text

        return Bombardment(key, num_projectiles, projectile_type_key)

# Generate structs based on TSV files extracted from pack files.
class TSVFactory(AbstractFactory):
    TYPE_INT   = 0
    TYPE_FLOAT = 1
    TYPE_STR   = 2
    TYPE_BOOL  = 3
    
    def __init__(self, logger, projectiles_tsv_path, projectile_bombardments_path, projectile_explosions_path, unit_special_abilities_path, vortex_tsv_path, special_ability_phases_path):
        super(TSVFactory, self).__init__(logger)
        logger.set_active_class("TSVFactory")

        self.ability_phase_localisation = {}
        if special_ability_phases_path and os.path.exists(special_ability_phases_path + ".loc"):
            self.read_phase_loc(special_ability_phases_path)
        
        # Explosions must be parsed before projectiles as projectile can reference an explosion
        if projectile_explosions_path:  self.parse_projectile_explosions(projectile_explosions_path)
        if projectiles_tsv_path:        self.parse_projectiles(projectiles_tsv_path)
        if projectile_explosions_path:  self.parse_bombardments(projectile_bombardments_path)
        if unit_special_abilities_path: self.parse_unit_special_abilities(unit_special_abilities_path)
        if vortex_tsv_path:             self.parse_vortexs(vortex_tsv_path)
        if special_ability_phases_path: self.parse_special_ability_phases(special_ability_phases_path)

        logger.reset_active_class()

    def read_phase_loc(self, path):
        loc = open(path + ".loc", "r")
        lines = loc.readlines()
        for i in range(2, len(lines)):
            line = lines[i].replace("\n", "").split("\t")
            key = line[0]
            localiastion = line[1]
            self.ability_phase_localisation[key] = localiastion.replace("\\\\", "\\")

        loc.close()

    def parse_tsv(self, path, constructor_func):        
        f = open(path, "r")
        
        lines = f.readlines()

        headers = lines[1].replace("/n", "").split("\t")
        header_type_info = self.find_column_type(lines, headers)

        for i in range(2, len(lines)):
            value_map = {}
            values = lines[i].replace("\n", "").split("\t")

            for j in range(len(headers)):
                value_map[headers[j]] = self.cast_to_type(values[j], headers[j], header_type_info)
            
            constructor_func(value_map)

        f.close()

    # Determine the datatype for columns automatically
    # For some reason exported tsv files sometimes treat values which are ints in assembly kit as floats
    # Hence a cast to int in object constuctor is required to prevent tooltips from displaying decimals 
    #e.g. damage as 16.0 instead of 16
    def find_column_type(self, lines, headers, debug=False):
        header_type_info = {}

        for i in range(2, len(lines)):
            line = lines[i].replace("\n", "").split("\t")
            for j in range(len(line)):
                value = line[j]
                try:
                    # Check if string is a valid int. Throws value error for floats.
                    int(value)
                    # prevent overwriting floats
                    if headers[j] not in header_type_info:
                        header_type_info[headers[j]] = self.TYPE_INT
                except ValueError:
                    # Not an int
                    try:
                        float(value)
                        header_type_info[headers[j]] = self.TYPE_FLOAT
                    except ValueError:
                        # Not a float/int
                        if value == "true" or value == "false": header_type_info[headers[j]] = self.TYPE_BOOL
                        else: header_type_info[headers[j]] = self.TYPE_STR
        
        return header_type_info

    def cast_to_type(self, value, header, type_info):
        if type_info[header]   == self.TYPE_INT:   return int(value)
        elif type_info[header] == self.TYPE_FLOAT: return float(value)
        elif type_info[header] == self.TYPE_STR:   
            if value == "": return None
            return value
        elif type_info[header] == self.TYPE_BOOL:  return value == "true"
        else: raise Exception("Unsupported data type for value: " + value)

    def parse_vortexs(self, path):
        self.parse_tsv(path, self.create_vortex)
        #print(self.vortexes)

    def parse_projectiles(self, path):
        self.parse_tsv(path, self.create_projectile)
        #print(self.projectiles)

    def parse_bombardments(self, path):
        self.parse_tsv(path, self.create_bombardment)
        #print(self.bombardments)

    def parse_projectile_explosions(self, path):
        self.parse_tsv(path, self.create_projectile_explosion)
        #print(self.projectile_explosions)

    def parse_unit_special_abilities(self, path):
        self.parse_tsv(path, self.create_special_unit_ability)
        #print(self.special_unit_abilities)

    def parse_special_ability_phases(self, path):
        self.parse_tsv(path, self.create_ability_phase)
        #print(self.ability_phases)

    def create_ability_phase(self, source):
        key = source["id"]
        dmg = source["damage_amount"]
        dmg_chance = source["damage_chance"]
        duration = source["duration"]
        frequency = source["hp_change_frequency"]

        # Join onscreen_name with the localiastion file.
        # This is included in xml files.
        onscreen_name = self.ability_phase_localisation["special_ability_phases_onscreen_name_" + key] or ""

        max_damaged_entities = source["max_damaged_entities"]
        
        ability_phase = AbilityPhase(key, dmg, dmg_chance, duration, frequency, max_damaged_entities, onscreen_name)

        self.ability_phases[ability_phase.key] = ability_phase
        self.log.debug("Adding ability phase: " +str(ability_phase))

    def create_vortex(self, source): 
        key = source["vortex_key"]
        dmg = source["damage"]
        dmgap = source["damage_ap"]
        is_fire_damage = source["ignition_amount"]
        is_magical = source["is_magical"]
        goal_radius = source["goal_radius"]
        start_radius = source["start_radius"]
        movement_speed = source["movement_speed"]
        expansion_speed = source["expansion_speed"]
        contact_effect = source["contact_effect"]

        vortex = Vortex(key, dmg, dmgap, is_fire_damage, is_magical, goal_radius, start_radius, movement_speed, expansion_speed, None, contact_effect)

        self.vortexes[vortex.key] = vortex
        self.log.debug("Adding vortex: " +str(vortex))

    def create_special_unit_ability(self, source): 
        key = source["key"]
        used_projectile_key = source["activated_projectile"]
        used_vortex_key = source["vortex"]
        used_bombardment_key = source["bombardment"]
        wind_up_time = source["wind_up_time"]
        is_passive = source["passive"]

        special_unit_ability = SpecialUnitAbility(key, used_projectile_key, used_vortex_key, used_bombardment_key, wind_up_time, is_passive)

        self.special_unit_abilities[special_unit_ability.key] = special_unit_ability
        self.log.debug("Adding special unit ability: " +str(special_unit_ability))


    def create_projectile_explosion(self, source): 
        key = source["key"]
        detonation_dmg = source["detonation_damage"]
        detonation_dmgap = source["detonation_damage_ap"]
        magical = source["is_magical"]
        
        projectile_explosion = ProjectileExplosion(key, detonation_dmg, detonation_dmgap, magical)

        if projectile_explosion.detonation_damage > 0 or projectile_explosion.detonation_damage_ap > 0:
            self.projectile_explosions[projectile_explosion.key] = projectile_explosion
            self.log.debug("Adding projectile explosion: " +str(projectile_explosion))

    def create_projectile(self, source):
        key = source["key"]
        dmg = source["damage"]
        dmgap = source["ap_damage"]
        bonus_v_large = source["bonus_v_large"]
        bonus_v_infantry = source["bonus_v_infantry"]
        is_fire_damage = source["ignition_amount"] > 0
        is_magical = source["is_magical"]
        projectile_number = source["projectile_number"]
        voley = source["shots_per_volley"]
        explosion_type = source["explosion_type"]
        contact_stat_effect = source["contact_stat_effect"]

        projectile = Projectile(key, dmg, dmgap, bonus_v_large, bonus_v_infantry, is_fire_damage, is_magical, projectile_number, voley, explosion_type, None, contact_stat_effect)

        projectile_explosion = projectile.get_projectile_explosion_if_exists(self.projectile_explosions)
        if projectile_explosion != None: 
            projectile.set_projectile_explosion_ref(projectile_explosion)

        self.log.debug("Adding projectile: " + str(projectile))
        self.projectiles[projectile.key] = projectile

    def create_bombardment(self, source): 
        key = source["bombardment_key"]
        num_projectiles = source["num_projectiles"]
        projectile_type_key = source["projectile_type"]

        bombardment = Bombardment(key, num_projectiles, projectile_type_key)
        self.log.debug("Adding bombardment: " + str(bombardment))
        self.bombardments[bombardment.key] = bombardment

        


# Classes for internal representation

class AbilityPhase:
    def __init__(self, key, dmg, dmg_chance, duration, frequency, max_damaged_entities, onscreen_name = ""):
        self.__key = key
        self.__dmg = dmg
        self.__dmg_chance = dmg_chance
        self.__duration = duration
        self.__frequency = frequency
        self.__onscreen_name = onscreen_name
        if self.__frequency == 0: self.__frequency = 1
        self.__max_damaged_entities = max_damaged_entities


    def get_damage_txt(self):
        max_damage = "infinity" if self.duration <= 0 else int((self.duration/self.frequency) * self.dmg)

        dmg_chance = int(100 * self.dmg_chance)
        if self.dmg > 0 and self.max_damaged_entities > 0:
            localisation = ""
            secondStr = "seconds" if self.frequency != 1 else "second"
            entityStr = "entities" if self.max_damaged_entities > 1 else "entity"
            time = int(self.frequency) if self.frequency.is_integer() else self.frequency
            if max_damage == "infinity":
                localisation = "Deals {dmg} damage to {entities} {entityStr} every {time} {secondStr} until all entities die.".format(dmg=self.dmg,entities=self.max_damaged_entities,entityStr=entityStr, time=time, secondStr=secondStr)
            elif dmg_chance == 0:
                localisation = "Deals {dmg} damage to {entities} {entityStr}. (Max damage: {maxDmg})".format(dmg=self.dmg, entities=self.max_damaged_entities, entityStr=entityStr, maxDmg=max_damage)
            else:
                localisation = "{chance}% chance to deal {dmg} damage per {time} {secondStr} to {entityCount} {entityStr}. (Max damage: {maxDmg})".format(chance=dmg_chance, dmg=self.dmg, entityCount=self.max_damaged_entities, entityStr=entityStr, maxDmg=max_damage, time=time, secondStr=secondStr)
            return [localisation, self.onscreen_name]
        return False

    @property
    def key(self): return self.__key
    @property
    def dmg(self): return self.__dmg
    @property
    def dmg_chance(self): return self.__dmg_chance
    @property
    def duration(self): return self.__duration
    @property
    def frequency(self): return self.__frequency
    @property
    def max_damaged_entities(self): return self.__max_damaged_entities
    @property
    def onscreen_name(self): return self.__onscreen_name

    def __str__(self): return ("AbilityPhase: {key} - dmg:{dmg}, chance:{chance}, duration:{duration}, frequency:{freq}, max_entity:{entity}"
        .format(key=self.key, dmg=self.dmg, chance=self.dmg_chance, duration=self.duration, freq=self.frequency, entity=self.max_damaged_entities))

    def __repr__(self): return self.__str__()

class Vortex:
    def __init__(self, key, dmg, dmgap, is_fire_damage, is_magical, goal_radius, start_radius, movement_speed, expansion_speed, ability_phase_ref, contact_effect):
        self.__key = key
        self.__dmg = int(dmg)     # cast tsv float to int @see TSVFactory.find_column_type
        self.__dmgap = int(dmgap) # cast tsv float to int @see TSVFactory.find_column_type
        self.__is_fire_damage = is_fire_damage
        self.__is_magical_damage = is_magical
        self.__goal_radius = goal_radius
        self.__start_radius = start_radius
        self.__movement_speed = movement_speed
        self.__expansion_speed = expansion_speed
        self.ability_phase = ability_phase_ref
        self.__contact_stat_effect = contact_effect

    def deals_no_damage(self):
        return self.dmg == self.dmgap == 0

    def set_ability_phase_ref(self, phase): self.ability_phase = phase

    def get_damage_txt(self):
        damageTxt = "Deals "
        if(self.__dmg <= 0 and self.__dmgap <= 0):
            damageTxt = "Deals no damage"
            return damageTxt
        else:
            magic_icon = "[[img:icon_dmg_flaming]][[/img]]" if self.__is_fire_damage else "[[img:icon_dmg_magical]][[/img]]" if self.__is_magical_damage else " non magical"
            if self.__dmg != 0: damageTxt += str(self.__dmg) +magic_icon +" "
            
            if self.__dmgap != 0:
                if self.__dmg != 0: damageTxt +="and " 
                damageTxt += str(self.__dmgap) + "[[img:icon_ap]][[/img]] "
        
        damageTxt += "damage to all entities hit in the AOE"
        return damageTxt


    def get_expanding_radius_txt(self):
        start_radius = int(self.start_radius) if self.start_radius.is_integer() else self.start_radius
        goal_radius = int(self.goal_radius) if self.goal_radius.is_integer() else self.goal_radius
        expansion_speed = int(self.expansion_speed) if self.expansion_speed.is_integer() else self.expansion_speed
        return "Damage radius expands from {srad} up to {grad} by {espeed} every second".format(srad=start_radius, grad=goal_radius, espeed=expansion_speed)

    def get_equal_radius_txt(self):
        assert self.goal_radius == self.start_radius
        goal_radius = int(self.goal_radius) if self.goal_radius.is_integer() else self.goal_radius
        return "Constant damage radius: {rad}".format(rad=goal_radius)

    @property
    def key(self): return self.__key
    @property
    def dmg(self): return self.__dmg
    @property
    def dmgap(self): return self.__dmgap
    @property
    def goal_radius(self): return self.__goal_radius
    @property
    def start_radius(self): return self.__start_radius
    @property
    def movement_speed(self): return self.__movement_speed
    @property
    def expansion_speed(self): return self.__expansion_speed
    @property
    def contact_stat_effect(self): return self.__contact_stat_effect

    def get_ability_phase_ref(self): return self.ability_phase
    
    
    def __str__(self): return ("Vortex: {key} - dmg:{dmg}, dmgap:{dmgap}".format(key=self.__key, dmg=self.__dmg, dmgap=self.__dmgap))

    def __repr__(self): return self.__str__()

class SpecialUnitAbility:
    def __init__(self, key, used_projectile_key, used_vortex_key, used_bombardment_key, wind_up_time, is_passive):
        self.__key = key
        self.__used_projectile_key = used_projectile_key
        self.__used_vortex_key = used_vortex_key
        self.__used_bombardment_key = used_bombardment_key
        self.__wind_up_time = wind_up_time
        self.__is_passive = is_passive
    
    @property
    def key(self): return self.__key
    @property
    def used_projectile_key(self): return self.__used_projectile_key
    @property
    def used_vortex_key(self): return self.__used_vortex_key
    @property
    def used_bombardment_key(self): return self.__used_bombardment_key
    @property
    def wind_up_time(self): return self.__wind_up_time
    @property
    def is_passive(self): return self.__is_passive

    def is_damaging_ability(self): return self.used_vortex_key != None or self.used_projectile_key != None or self.used_bombardment_key != None

    def __str__(self): return ("SpecialUnitAbility: {key} - used_projectile:{proj}, used_vortex:{vortex}, used_bombardment:{bomb}"
        .format(key=self.__key, proj=self.__used_projectile_key, vortex=self.__used_vortex_key, bomb=self.__used_bombardment_key))

class ProjectileExplosion:
    def __init__(self, key, detonation_dmg, detonation_dmgap, is_magical):
        self.__key = key
        self.__detonation_dmg = int(detonation_dmg)      # cast tsv float to int @see TSVFactory.find_column_type
        self.__detonation_dmgap = int(detonation_dmgap)  # cast tsv float to int @see TSVFactory.find_column_type
        self.__magical = is_magical

    def get_detonation_string(self):
        detonation_loc = "Detonation damage (per projectile): " if self.__magical else "Detonation damage (per projectile & non-magical): "
        magic_icon = "" if self.__magical == False else "[[img:icon_dmg_magical]][[/img]]"
        if self.__detonation_dmg > 0: detonation_loc += str(self.__detonation_dmg) +magic_icon
        if self.__detonation_dmgap > 0:
            if self.__detonation_dmg > 0: detonation_loc += " and " + str(self.__detonation_dmgap) +"[[img:icon_ap]][[/img]]"
            else: detonation_loc += str(self.__detonation_dmgap) + "[[img:icon_ap]][[/img]]"
        return detonation_loc

    @property
    def key(self): return self.__key
    @property
    def detonation_damage(self): return self.__detonation_dmg
    @property
    def detonation_damage_ap(self): return self.__detonation_dmgap
    @property
    def is_magical(self): return self.__magical

    def __str__(self):
        return ("ProjectileExplosion: {key} - det_dmg:{detdmg}, det_dmgap:{detdmgap}, magical:{magical}"
        .format(key=self.__key, detdmg=self.__detonation_dmg, detdmgap=self.__detonation_dmgap, magical=self.__magical))

    def __repr__(self): return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__key == other.key and self.__detonation_dmg == other.detonation_damage and self.__detonation_dmgap == other.detonation_damage_ap and self.__magical == other.is_magical
        return False

class Projectile:
    def __init__(self, key, dmg, dmgap, b_v_L, b_v_I, is_fire, is_magical, proj_num, voley, explosion_type, proj_explosion_ref, contact_effect):
        self.__key = key
        self.__dmg = int(dmg)      # cast tsv float to int @see TSVFactory.find_column_type
        self.__dmgap = int(dmgap)  # cast tsv float to int @see TSVFactory.find_column_type
        self.__bonus_v_large = b_v_L 
        self.__bonus_v_infantry = b_v_I
        self.__is_fire_damage = is_fire
        self.__is_magical = is_magical
        self.__projectile_number = proj_num
        self.__voley = voley
        self.__explosion_type = explosion_type
        self.ref_projectile_explosion = proj_explosion_ref
        self.__contact_stat_effect = contact_effect

    def set_projectile_explosion_ref(self, detonation):
        assert detonation != None
        self.ref_projectile_explosion = detonation

    def get_projectile_explosion_ref(self): return self.ref_projectile_explosion

    
    def get_projectile_explosion_if_exists(self, projectile_explosion_map):
        if self.__explosion_type in projectile_explosion_map: return projectile_explosion_map[self.__explosion_type]
        return None

    def is_used_in_bombardment(self, bombardment_map):
        bombardment_uses = []
        for bombardment in bombardment_map.values():
            if bombardment.projectile_type_key == self.__key or bombardment.projectile_type_key == self.__key.replace("_upgraded",""):
                bombardment_uses.append(bombardment)
        return bombardment_uses

    def get_damage_txt(self):
        damageTxt = create_damage_string(self.dmg, self.dmgap, self.__is_fire_damage, self.__is_magical)
        if damageTxt == False: return False
        projectileTxt = "a projectile" if self.__projectile_number == 1 else str(self.__projectile_number) + " projectiles, each"
        if self.__voley > 1:
            if self.__projectile_number == 1:
                projectileTxt = "a projectile in " + str(self.__voley) +" voleys each"
            else:
                projectileTxt = str(self.__projectile_number) + " projectiles in " + str(self.__voley) +" voleys, each"
        return ("Launch {projectileTxt} dealing {damageTxt} ").format(projectileTxt=projectileTxt, damageTxt=damageTxt)


        

    def __str__(self):
        return ("Projectile: {key} - dmg:{dmg}, dmgap:{dmgap}, b_v_L:{bvl}, b_v_I:{bvi}, is_fire_damage:{fire}, magical:{magical}, #proj:{projnum}, voley:{voley}, detonation_ref:{dref}"
            .format(key=self.__key, dmg=self.__dmg, dmgap=self.__dmgap, bvl=self.__bonus_v_large, bvi=self.__bonus_v_infantry, magical=self.__is_magical, fire=self.__is_fire_damage,
            projnum=self.__projectile_number, voley=self.__voley, dref=self.ref_projectile_explosion))

    def __repr__(self): return self.__str__()

    @property
    def key(self): return self.__key
    @property
    def dmg(self): return self.__dmg
    @property
    def dmgap(self): return self.__dmgap
    @property
    def bonus_v_large(self): return self.__bonus_v_large
    @property
    def bonus_v_infantry(self): return self.__bonus_v_infantry
    @property
    def is_fire_damage(self): return self.__is_fire_damage
    @property
    def is_magical_damage(self): return self.__is_magical
    @property
    def projectile_number(self): return self.__projectile_number
    @property
    def voley(self): return self.__voley
    @property
    def explosion_type(self): return self.__explosion_type
    @property
    def contact_stat_effect(self): return self.__contact_stat_effect

class Bombardment:
    def __init__(self, key, num_proj, proj_type_key):
        self.__key = key
        self.__num_projectiles = num_proj
        self.__projectile_type_key = proj_type_key

    def get_bombardment_string(self, projectile): 
        is_projectiles_plural = ""
        additional_sub_projectile_hint = "" if projectile.projectile_number == 1 else " (each projectile launches " + str(projectile.projectile_number) +" projectiles)"
        if (self.__num_projectiles > 1): is_projectiles_plural = "projectiles" +additional_sub_projectile_hint+ ", each"
        else: is_projectiles_plural = "projectile " + additional_sub_projectile_hint
        damageTxt = create_damage_string(projectile.dmg, projectile.dmgap, projectile.is_fire_damage, projectile.is_magical_damage)

        if damageTxt == False: return False
        return "Launch {numproj} {projectile_str} dealing {damageTxt}".format(numproj=self.__num_projectiles, projectile_str=is_projectiles_plural, damageTxt=damageTxt)


    def get_projectile(self, projectile_map): return projectile_map[self.__projectile_type_key]
    
    @property
    def key(self): return self.__key
    @property
    def num_projectiles(self): return self.__num_projectiles
    @property
    def projectile_type_key(self): return self.__projectile_type_key

    def __str__(self):
        return ("Bombardment: {key} - #proj:{numproj}, projectile_used:{projtype}"
        .format(key=self.__key, numproj=self.__num_projectiles, projtype=self.__projectile_type_key))

    def __repr__(self): return self.__str__()
