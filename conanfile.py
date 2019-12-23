
import requests
import json
from conans import ConanFile, tools
import datetime
import time
import os
import shutil


def get_timestamp(org, repo, commit):
    url = "https://api.github.com/repos/{}/{}/commits/{}".format(org, repo, commit)
    r = requests.get(url).json()
    sha = r["sha"]
    date = datetime.datetime.strptime(r["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(time.mktime(date.timetuple()))
    return sha, timestamp


commit = "e4ad265339f17042a86227bfb44f9d5d7dee5ba4"
sha, timestamp = get_timestamp("GodotNativeTools", "godot-cpp", commit)


class GodotCpp(ConanFile):
    name = "godot-cpp"
    commit = "e4ad265339f17042a86227bfb44f9d5d7dee5ba4"
    version = "3.1-{}".format(timestamp)  # 'master' branch uses semver 0.0.0-<timestamp> (will allow version ranges)

    settings = "os", "arch", "compiler", "build_type"

    def source(self):
        tools.get("https://github.com/GodotNativeTools/godot-cpp/archive/{}.tar.gz".format(commit),
                  md5="011aaada9b09b35d2c032b120228ec33")
        shutil.move("{}-{}".format(self.name, commit), self.name)

        # Clone the headers too
        headers_commit = "98ee82599dfe07e17983ad831f5e9ac41068667f"
        tools.get("https://github.com/GodotNativeTools/godot_headers/archive/{}.tar.gz".format(headers_commit),
                  md5="fb6ce42f83dab25e6e26cd780043e846")
        target_directory = os.path.join(self.name, "godot_headers")
        shutil.rmtree(target_directory)
        shutil.move("godot_headers-{}".format(headers_commit), target_directory)

    @property
    def platform(self):
        if self.settings.os == "Macos":
            return "osx"
        else:
            return str(self.settings.os).lower()

    @property
    def arch(self):
        return {"x86": "32", "x86_64": "64"}.get(str(self.settings.arch))

    def build(self):
        #debug_opt = '--debug-build' if self.settings.build_type == 'Debug' else ''
        debug_opt = 'target={}'.format(str(self.settings.build_type).lower())
        self.run('scons -C {} platform={} generate_bindings=yes {}'.format(self.name, self.platform, debug_opt))

    def package(self):
        self.copy("*.h", dst="include", src=os.path.join(self.name, "godot_headers"))
        self.copy("*.hpp", dst="include", src=os.path.join(self.name, "include"))
        self.copy("*.a", dst="lib", src=os.path.join(self.name, "bin"), keep_path=False)
        #self.copy("*.lib", dst="lib", keep_path=False)
        #self.copy("*.dll", dst="bin", keep_path=False)
        #self.copy("*.dylib*", dst="lib", keep_path=False)
        #self.copy("*.so", dst="lib", keep_path=False)
        
    def package_info(self):
        # TODO: It looks like that if the name already has dots, the linker doesn't add suffix for .a, .so
        lib = "libgodot-cpp.{}.{}.{}.a".format(self.platform, 
                                               str(self.settings.build_type).lower(),
                                               self.arch)

        self.cpp_info.libs = [lib]
        self.cpp_info.includedirs = ["include", "include/core", "include/gen"]

