import os
import re


def git_pull(src, branch, des):
    project_name = re.findall(r"^.*/(.*).git", src)[0]
    if not os.path.exists(des):
        os.mkdir(des)
    os.chdir(des)
    if not os.path.exists(project_name):
        os.system(f"git clone -b {branch} {src}")
    else:
        os.chdir(project_name)
        os.system(f"git checkout {branch}")
        os.system("git pull")
    return project_name
