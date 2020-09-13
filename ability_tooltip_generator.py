import sys
import hashlib
import os

class AbilityTooltipGenerator:
    # TAG -> [Reference, Sort order priority] (Higher = lower in the game UI tooltip)
    TAG_DAMAGE_TOOLTIP = ["_th_damage_tooltip", 190]
    TAG_PHASE_TOOLTIP = ["_th_phase_damage_tooltip", 191]
    TAG_DETONATION_DAMAGE_TOOLTIP = ["_th_detonation_damage_tooltip", 192]
    TAG_BONUS_V_LARGE = ["_th_damage_bonus_v_large", 193]
    TAG_MOVEMENT_SPEED = ["_th_movement_speed", 194]
    TAG_EQUAL_RADIUS = ["_th_equal_radius", 195]
    TAG_EXPANDING_RADIUS = ["_th_expanding_radius", 195]
    TAG_WIND_UP_TINE = ["_th_wind_up_time", 196]
    TAG_ON_CONTACT = ["_th_on_projectile_cont", 197]

    def __init__(self, log):
        self.arr_tooltips = {} # Map<key+tag, tooltip> probably should be Map<key, Map<tag, tooltip>> where tooltip is in the form {key, localisation, tag}
        self.log = log

    def dump(self):
        self.log.set_active_class("AbilityTooltipGenerator")
        self.log.debug(str(self.__dict__.keys()))
        self.log.debug(str((AbilityTooltipGenerator.__dict__)))

        self.log.debug("~~~~~~~~~~~~~~~~~~ DUMPING AbilityTooltipGenerator ~~~~~~~~~~~~~~~~~~")
        for tooltip_key in self.arr_tooltips:
            tooltip = self.arr_tooltips[tooltip_key]
            self.log.debug(tooltip_key + " | "+str(tooltip))

    # Return true and an array of tooltips if any tooltips have been created for the specified key.
    # Otherwise returns false
    def contains_key(self, key):
        found = False
        tooltips = []
        for var in AbilityTooltipGenerator.__dict__:
            if var.startswith("TAG"):
                tag = AbilityTooltipGenerator.__dict__[var]
                if key + tag[0] in self.arr_tooltips:
                    if tag != AbilityTooltipGenerator.TAG_WIND_UP_TINE: #hack
                        found = True
                        tooltips.append(self.arr_tooltips[key + tag[0]])


        return [found, tooltips]

    # Returns true if a damage tooltip exists for the key
    def contains_damage_tooltip(self, key):
        return key + self.TAG_DAMAGE_TOOLTIP[0] in self.arr_tooltips

    # Returns true if a detonation tooltip exists for the key
    def contains_detonation_tooltip(self, key):
        return key + self.TAG_DETONATION_DAMAGE_TOOLTIP[0] in self.arr_tooltips

    def _add_tooltip(self, tooltip):
        key = tooltip["key"] + tooltip["tag"][0]

        # Has been used to debug logic errors
        if key in self.arr_tooltips and tooltip["localisation"] != self.arr_tooltips[key]["localisation"]:
            print("Warning already added: " + key)
            print("New localisation: " + tooltip["localisation"])
            print("Current localisation: " +self.arr_tooltips[key]["localisation"])
            return
        
        self.log.debug("Added tooltip: " +str(tooltip))
        self.arr_tooltips[key] = tooltip

    def add_damage_tooltip(self, key, localisation):
        self._add_tooltip({"key":key, "localisation": localisation, "tag": self.TAG_DAMAGE_TOOLTIP})

    def add_bonus_v_large_tooltip(self, key, stramount):
        self._add_tooltip({"key":key, "localisation":"Bonus versus large: " +stramount, "tag": self.TAG_BONUS_V_LARGE})

    def add_detonation_damage_tooltip_with_local(self, key, localisation):
        self._add_tooltip({"key":key, "localisation": localisation, "tag": self.TAG_DETONATION_DAMAGE_TOOLTIP})

    def add_phase_tooltip(self, key, localisation):
        self._add_tooltip({"key":key, "localisation":localisation, "tag": self.TAG_PHASE_TOOLTIP})

    def add_detonation_damage_tooltip(self, key, explosion):
        dmg = explosion["detonation_dmg"]
        dmgap = explosion["detonation_dmgap"]
        is_magical = explosion["is_magical"]
        assert (dmg > 0 or dmgap > 0) and type(is_magical) == bool

        localisation = "Detonation damage (per projectile & magical): " if is_magical else "Detonation damage (per projectile & non-magical): "

        if dmg > 0: localisation += str(dmg)
        if dmgap > 0:
            if dmg > 0: localisation += ", " + str(dmgap) + " AP"
            else: localisation += str(dmgap) +" AP"
        
        self._add_tooltip({"key":key, "localisation":localisation, "tag": self.TAG_DETONATION_DAMAGE_TOOLTIP})

    def add_equal_radius_tooltip(self, key, localisation):
        self._add_tooltip({"key":key, "localisation":localisation, "tag":self.TAG_EQUAL_RADIUS})

    def add_expanding_radius_tooltip(self, key, localisation):
        self._add_tooltip({"key":key, "localisation":localisation, "tag":self.TAG_EXPANDING_RADIUS})

    def add_wind_up_time_tooltip(self, key, localisation):
        self._add_tooltip({"key":key, "localisation":localisation, "tag":self.TAG_WIND_UP_TINE})

    def add_on_contact_tooltip(self, key, localisation):
        self._add_tooltip({"key": key, "localisation": localisation, "tag": self.TAG_ON_CONTACT})

    def add_tooltips(self, type, detonation, damageTxt, log):
        if damageTxt != False:
            log.debug("Added damage tooltip with key: {key} and text: {text}".format(key=type.key,text=damageTxt))
            self.add_damage_tooltip(type.key, damageTxt)
        else:
            log.debug("Failed to add damage tooltip for {key}. \nType:{type}\nDetonation:{detonation}".format(key=type.key, type=type, detonation=detonation))
        if detonation != None:
            log.debug("Added detonation tooltip with key: {key} and text: {text}".format(key=type.key,text=detonation.get_detonation_string()))
            self.add_detonation_damage_tooltip_with_local(type.key, detonation.get_detonation_string())
        else:
            log.debug("Failed to add detonation tooltip for {key}. \nType:{type}\nDetonation:{detonation}".format(key=type.key, type=type, detonation=detonation))


    def _create_tooltip_ref(self, tooltip):
        return tooltip["key"] + tooltip["tag"][0]

    def _format_localisation(self, loc):
        localisation = ""
        if isinstance(loc, list): localisation = loc[0]
        else: localisation = loc
        return "[[col:yellow]]" + localisation + "[[/col]]"
    
    def _format_contact_localisation(self, loc):
        onscreen_loc = loc[1].replace(r"\n", r"\\n")
        return onscreen_loc + self._format_localisation(loc)

    def generate_tsv_files(self, log):
        log.set_active_class("AbilityTooltipGenerator")
        log.debug("~~~~~~~~~~~~~~~~~~~~ PRINTING TOOLTIPS ~~~~~~~~~~~~~~~~~~~~")
        for tooltip in self.arr_tooltips:
            log.debug(str(tooltip))

        if not os.path.isdir("./out"):
            os.mkdir("out")

        log.info("Started generating tsv files.")
        tooltip_sort_order_file = open("out/unit_abilities_additional_ui_effects_tables.tsv", "w", newline="")
        tooltip_sort_order_file.write("unit_abilities_additional_ui_effects_tables\t2\n")
        tooltip_sort_order_file.write("key\tsort_order\n")

        ability_to_tooltip_map_file = open("out/unit_abilities_to_additional_ui_effects_juncs_tables.tsv", "w", newline="")
        ability_to_tooltip_map_file.write("unit_abilities_to_additional_ui_effects_juncs_tables\t0\n")
        ability_to_tooltip_map_file.write("ability\teffect\n")

        localisaton_file = open("out/th_damage_loc.tsv", "w", newline="")
        localisaton_file.write("Loc PackedFile\t1\n")
        localisaton_file.write("key\ttext\ttooltip\n")

        for tooltip in self.arr_tooltips.values():
            log.info("Saving tooltip: " + str(tooltip))
            tooltip_ref = self._create_tooltip_ref(tooltip)
            tooltip_sort_order_file.write(tooltip_ref +"\t" + str(tooltip["tag"][1]) +"\n")
            ability_to_tooltip_map_file.write(tooltip['key'] +"\t" + tooltip_ref +"\n")
            if "contact" in tooltip_ref:
                localisaton_file.write('special_ability_phases_onscreen_name_' + tooltip["key"] +'\t' + self._format_contact_localisation(tooltip['localisation']) +'\ttrue\n')
            else:
                localisaton_file.write('unit_abilities_additional_ui_effects_localised_text_' + tooltip_ref +'\t' + self._format_localisation(tooltip['localisation']) +'\ttrue\n')

        tooltip_sort_order_file.close()
        ability_to_tooltip_map_file.close()
        localisaton_file.close()
        log.info("Finished generating tsv files.")
        log.reset_active_class()


    # Compare hashes of generated files with existing files (must end with "_test.tsv").
    # Used to test if refactoring has changed the output.
    def test_output_integrity(self, test_ui_effects = True, test_ui_effects_juncs = True, test_loc = True):
        if test_ui_effects: assert self.valid_hash("unit_abilities_additional_ui_effects_tables"), "UE effects table mismatch"
        if test_ui_effects_juncs: assert self.valid_hash("unit_abilities_to_additional_ui_effects_juncs_tables"), "UI effects juncs table mismatch"
        if test_loc: assert self.valid_hash("th_damage_loc"), "Localisation mismatch"
        print("Hashes match")

    def valid_hash(self, file):
        h1 = self.hash(file +".tsv")
        h2 = self.hash(file +"_test" + ".tsv")
        return h1["md5"] == h2["md5"] and h1["sha1"] == h2["sha1"] and h1["sha384"] == h2["sha384"]

    def hash(self, file):
        buffer_size = 65536
        sha1 = hashlib.sha1()
        sha384 = hashlib.sha384()
        md5 = hashlib.md5()
        with open(file, "rb") as f:
            data = ""
            while not data:
                data = f.read(buffer_size)
                sha1.update(data)
                md5.update(data)
                sha384.update(data)
        return {"md5": md5.hexdigest(), "sha1": sha1.hexdigest(), "sha384": sha384.hexdigest()}

