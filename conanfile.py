
import requests
import json
from conans import ConanFile, tools
import datetime
import time
import os


def get_last_commit(org, repo, branch):
    url = "https://api.github.com/repos/{}/{}/commits/{}".format(org, repo, branch)
    r = requests.get(url).json()
    sha = r["sha"]
    date = datetime.datetime.strptime(r["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(time.mktime(date.timetuple()))
    return sha, timestamp

sha, timestamp = get_last_commit("GodotNativeTools", "godot-cpp", "master")


class GodotCpp(ConanFile):
    name = "godot-cpp"
    version = "0.0.0-{}".format(timestamp)  # 'master' branch uses semver 0.0.0-<timestamp> (will allow version ranges)

    settings = "os", "arch", "compiler", "build_type"

    def source(self):
        git = tools.Git(folder=self.name)
        git.clone("https://github.com/GodotNativeTools/godot-cpp.git")
        git.checkout(sha)
        git.run("submodule update --init --recursive")

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
        self.copy("gdnative_api_struct.gen.h", dst="include", src=os.path.join(self.name, "godot_headers"))
        self.copy("*.hpp", dst="include", src=os.path.join(self.name, "include"))
        self.copy("*.a", dst="lib", src=os.path.join(self.name, "bin"), keep_path=False)
        #self.copy("*.lib", dst="lib", keep_path=False)
        #self.copy("*.dll", dst="bin", keep_path=False)
        #self.copy("*.dylib*", dst="lib", keep_path=False)
        #self.copy("*.so", dst="lib", keep_path=False)
        
    def package_info(self):
        lib = "libgodot-cpp.{}.{}.{}".format(self.platform, 
                                            str(self.settings.build_type).lower(),
                                            self.arch)

        self.cpp_info.libs = [lib]

