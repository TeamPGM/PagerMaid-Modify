import os
import traceback
import yaml


class Lang:
    def __init__(self, locale):
        self.locales = self.get_available_locales()
        if locale not in self.locales:
            locale = "zh-cn"
            print(f"{locale} is not a valid locale , using zh-cn instead")
        self.locale = locale
        self.text = self.load_text()
        self.all_locales = self.load_locales()
        self.help_msg = {}
        for i in self.locales:
            self.help_msg[i] = f"`{i}` - {self.all_locales[i]['name']} ( {self.all_locales[i]['nativeName']} )"

    @staticmethod
    def get_available_locales() -> list:
        return sorted([lang.split(".")[0] for lang in os.listdir("languages/built-in")
                       if not lang.endswith("locales.yml")])

    def load_text(self) -> dict:
        text = {}
        for locale in self.locales:
            with open(f"languages/built-in/{locale}.yml", "r", encoding="utf-8") as yaml_file:
                text.update({locale: yaml.load(yaml_file, Loader=yaml.FullLoader)})
        try:
            with open(f"languages/custom.yml", "r", encoding="utf-8") as x:
                lang_temp = yaml.safe_load(x)
            for key, value in lang_temp.items():
                text["custom"][key] = value
        except FileNotFoundError:
            pass
        except Exception as e:
            traceback.print_exc()
        return text

    @staticmethod
    def load_locales():
        with open(f"languages/built-in/locales.yml", "r", encoding="utf-8") as yaml_file:
            return yaml.load(yaml_file, Loader=yaml.FullLoader)

    def get(self, text):
        try:
            return self.text["custom"][text]
        except KeyError:
            try:
                return self.text[self.locale][text]
            except KeyError:
                try:
                    return self.text["zh-cn"][text]
                except KeyError:
                    return text
